"""
Pydantic v2 schema for LLM-authored StratagemDSL strategies.

This mirrors the exact pattern already used by this codebase for Galaxy
codegen (smac-ast's HTN `GalaxyScript`, driven with Claude's
tool-use / OpenAI function-calling): every node is a `BaseModel` with
`extra="forbid"` (required for OpenAI structured-output / strict JSON
schema mode), expression variants are a discriminated union on an explicit
`kind` field (Pydantic needs a real discriminator; the hand-written
dataclasses in `model.py` distinguish variants via `isinstance` instead),
and every node has a `to_model()` method that converts into the exact
`stratagemdsl.core.model` dataclasses already consumed by `unparse()` /
`Validator` / `backend.galaxy.lower_to_galaxy()`.

This is the ONLY new surface a real LLM call has to hit correctly -- once
we have a `model.Strategy`, every downstream step (unparse -> ANTLR4
re-parse -> Validator -> Galaxy lowering -> smac-ast compile) is the exact
same, already-verified pipeline used by the simulated generator.
"""
from __future__ import annotations

import json
from typing import Annotated, Literal, Optional, Union

from pydantic import BaseModel, ConfigDict, Field, field_validator

from stratagemdsl.core import model as M
from stratagemdsl.registry.contracts import REGISTRY


class Node(BaseModel):
    model_config = ConfigDict(extra="forbid")


# ----------------------------- Expressions -----------------------------

class NameExprS(Node):
    kind: Literal["name"] = "name"
    name: str = Field(description="Reference to a world entity, derived fact, or plan-node id.")

    def to_model(self) -> M.Expr:
        return M.NameExpr(self.name)


class BoolExprS(Node):
    kind: Literal["bool"] = "bool"
    value: bool

    def to_model(self) -> M.Expr:
        return M.BoolExpr(self.value)


class NumberExprS(Node):
    kind: Literal["number"] = "number"
    value: float

    def to_model(self) -> M.Expr:
        return M.NumberExpr(self.value)


class StringExprS(Node):
    kind: Literal["string"] = "string"
    value: str

    def to_model(self) -> M.Expr:
        return M.StringExpr(self.value)


class CallExprS(Node):
    kind: Literal["call"] = "call"
    name: str = Field(
        description="Callable API name from the canonical contract registry; context-specific signatures are checked by Validator.",
        json_schema_extra={"enum": sorted({name for _, name in REGISTRY})},
    )
    args: list["ExprS"] = Field(default_factory=list)

    @field_validator("name")
    @classmethod
    def registered_api(cls, value: str) -> str:
        if value not in {name for _, name in REGISTRY}:
            raise ValueError(f"unknown StratagemDSL API '{value}'; see the API contract registry")
        return value

    def to_model(self) -> M.Expr:
        return M.CallExpr(self.name, [a.to_model() for a in self.args])


class UnaryExprS(Node):
    kind: Literal["unary"] = "unary"
    op: Literal["not", "-"]
    operand: "ExprS"

    def to_model(self) -> M.Expr:
        return M.UnaryExpr(self.op, self.operand.to_model())


class BinaryExprS(Node):
    kind: Literal["binary"] = "binary"
    op: Literal["and", "or", "implies", "==", "!=", "<=", ">=", "<", ">", "+", "-", "*", "/"]
    left: "ExprS"
    right: "ExprS"

    def to_model(self) -> M.Expr:
        return M.BinaryExpr(self.op, self.left.to_model(), self.right.to_model())


ExprS = Annotated[
    Union[NameExprS, BoolExprS, NumberExprS, StringExprS, CallExprS, UnaryExprS, BinaryExprS],
    Field(discriminator="kind"),
]
CallExprS.model_rebuild()
UnaryExprS.model_rebuild()
BinaryExprS.model_rebuild()


# ----------------------------- World -----------------------------

class EntityDeclS(Node):
    kind_: Literal["force", "asset", "region", "route"] = Field(alias="entity_kind")
    name: str
    side: Optional[Literal["ally", "enemy", "neutral"]] = None
    role: Optional[str] = None
    under_construction: Optional[bool] = None
    initial: Optional[bool] = None

    model_config = ConfigDict(extra="forbid", populate_by_name=True)

    def to_model(self) -> M.EntityDecl:
        props: dict = {}
        if self.side is not None:
            props["side"] = self.side
        if self.role is not None:
            props["role"] = self.role
        if self.under_construction is not None:
            props["under_construction"] = self.under_construction
        if self.initial is not None:
            props["initial"] = self.initial
        return M.EntityDecl(self.kind_, self.name, props)


class IntentS(Node):
    pattern: Optional[str] = None
    pattern_bindings: dict[str, str] = Field(default_factory=dict)
    primary: "ExprS"
    secondary: Optional["ExprS"] = None
    success: "ExprS"
    failure: "ExprS"

    def to_model(self) -> M.Intent:
        return M.Intent(
            self.pattern,
            self.primary.to_model(),
            self.secondary.to_model() if self.secondary else None,
            self.success.to_model(),
            self.failure.to_model(),
            self.pattern_bindings,
        )


class DerivedFactS(Node):
    name: str
    expr: "ExprS"

    def to_model(self) -> M.DerivedFact:
        return M.DerivedFact(self.name, self.expr.to_model())


# ----------------------------- Plan graph -----------------------------

class ActionBlockS(Node):
    mode: Literal["sequence", "parallel"] = "sequence"
    actions: list[CallExprS] = Field(default_factory=list)

    def to_model(self) -> M.ActionBlock:
        return M.ActionBlock(self.mode, [a.to_model() for a in self.actions])


class PhaseS(Node):
    node_type: Literal["phase"] = "phase"
    id: str
    purpose: str
    actors: list[str] = Field(default_factory=list)
    focus: list[str] = Field(default_factory=list)
    entry: Optional["ExprS"] = None
    actions: Optional[ActionBlockS] = None
    invariant: Optional["ExprS"] = None
    exit: Optional["ExprS"] = None
    terminal: Optional[Literal["success", "failure"]] = None
    repeatable: bool = False

    def to_model(self) -> M.Phase:
        return M.Phase(
            id=self.id, purpose=self.purpose, actors=self.actors, focus=self.focus,
            entry=self.entry.to_model() if self.entry else None,
            actions=self.actions.to_model() if self.actions else None,
            invariant=self.invariant.to_model() if self.invariant else None,
            exit=self.exit.to_model() if self.exit else None,
            terminal=self.terminal,
            repeatable=self.repeatable,
        )


class JoinS(Node):
    node_type: Literal["join"] = "join"
    id: str
    policy: Literal["all", "any", "atleast"]
    quorum: Optional[int] = None

    def to_model(self) -> M.Join:
        return M.Join(self.id, self.policy, self.quorum)


class PlaceS(Node):
    """v0.6 token place (budget, counter, semaphore)."""
    node_type: Literal["place"] = "place"
    id: str
    purpose: str = ""
    tokens: int = 0
    capacity: Optional[int] = None

    def to_model(self) -> M.Place:
        return M.Place(self.id, self.purpose, self.tokens, self.capacity)


PlanNodeS = Annotated[Union[PhaseS, JoinS, PlaceS], Field(discriminator="node_type")]


class ArcS(Node):
    place: str
    weight: int = 1
    kind: Literal["normal", "read", "inhibit"] = "normal"

    def to_model(self) -> M.Arc:
        return M.Arc(self.place, self.weight, self.kind)


class TransitionS(Node):
    id: str
    source: str
    target: str
    event: Optional[CallExprS] = None
    guard: Optional["ExprS"] = None
    actions: Optional[ActionBlockS] = None
    priority: int = 10
    inputs: list[ArcS] = Field(default_factory=list, description="v0.6: all input arcs; empty means [source]")
    outputs: list[ArcS] = Field(default_factory=list, description="v0.6: all output arcs; empty means [target]")

    def to_model(self) -> M.Transition:
        return M.Transition(
            id=self.id, source=self.source, target=self.target,
            event=self.event.to_model() if self.event else None,
            guard=self.guard.to_model() if self.guard else None,
            actions=self.actions.to_model() if self.actions else None,
            priority=self.priority,
            inputs=[a.to_model() for a in self.inputs],
            outputs=[a.to_model() for a in self.outputs],
        )


class PlanS(Node):
    start: list[str]
    nodes: list[PlanNodeS]
    transitions: list[TransitionS]

    def to_model(self) -> M.Plan:
        return M.Plan(self.start, [n.to_model() for n in self.nodes], [t.to_model() for t in self.transitions])


# ----------------------------- Binding -----------------------------

class BindingCallS(Node):
    value_type: Literal["call"] = "call"
    name: str = Field(description="unit_group | unit | group_slice | circle | route_path | setup | ...")
    args: list["BindingArgS"] = Field(default_factory=list)

    def to_model(self) -> M.BindingCall:
        return M.BindingCall(self.name, [a.to_model() for a in self.args])


BindingValueS = Annotated[
    Union[BindingCallS, "BindingLiteralS", "BindingListS"],
    Field(discriminator="value_type"),
]


class BindingLiteralS(Node):
    value_type: Literal["literal"] = "literal"
    string_value: Optional[str] = None
    number_value: Optional[float] = None
    bool_value: Optional[bool] = None

    def to_model(self):
        if self.string_value is not None:
            return self.string_value
        if self.number_value is not None:
            return self.number_value
        if self.bool_value is not None:
            return self.bool_value
        raise ValueError("BindingLiteralS has no value set")


class BindingListS(Node):
    value_type: Literal["list"] = "list"
    items: list[BindingValueS] = Field(default_factory=list)

    def to_model(self):
        return [item.to_model() for item in self.items]


class BindingArgS(Node):
    name: Optional[str] = None
    value: BindingValueS

    def to_model(self) -> M.BindingArg:
        return M.BindingArg(self.name, self.value.to_model())


BindingCallS.model_rebuild()
BindingListS.model_rebuild()


class BindingS(Node):
    name: str
    value: BindingValueS

    def to_model(self) -> M.Binding:
        return M.Binding(self.name, self.value.to_model())


# ----------------------------- Strategy -----------------------------

class StrategyS(Node):
    """Top-level schema an LLM call must return (Anthropic tool `input_schema`
    or OpenAI function `parameters`)."""

    name: str = Field(description="snake_case strategy identifier, must be a valid StratagemDSL ID.")
    world: list[EntityDeclS]
    initial: list["ExprS"] = Field(default_factory=list)
    intent: IntentS
    derived: list[DerivedFactS] = Field(default_factory=list)
    plan: PlanS
    backend: Optional[str] = "sc2"
    bindings: list[BindingS] = Field(default_factory=list)

    def to_model(self) -> M.Strategy:
        return M.Strategy(
            name=self.name,
            world=[e.to_model() for e in self.world],
            initial=[e.to_model() for e in self.initial],
            intent=self.intent.to_model(),
            derived=[d.to_model() for d in self.derived],
            plan=self.plan.to_model(),
            backend=self.backend,
            bindings=[b.to_model() for b in self.bindings],
        )


StrategyS.model_rebuild()


def strategy_json_schema() -> dict:
    """The JSON schema to hand to a real LLM call's tool/function definition."""
    return StrategyS.model_json_schema()


def strategy_to_schema_dict(s: M.Strategy) -> dict:
    """model.Strategy -> plain dict matching StrategyS's shape, so few-shot
    examples in the prompt can be built directly from existing .strat seeds
    instead of being hand-written twice."""
    return json.loads(_to_schema_json(s))


def _expr_to_s(e: M.Expr) -> dict:
    if isinstance(e, M.NameExpr):
        return {"kind": "name", "name": e.name}
    if isinstance(e, M.BoolExpr):
        return {"kind": "bool", "value": e.value}
    if isinstance(e, M.NumberExpr):
        return {"kind": "number", "value": e.value}
    if isinstance(e, M.StringExpr):
        return {"kind": "string", "value": e.value}
    if isinstance(e, M.CallExpr):
        return {"kind": "call", "name": e.name, "args": [_expr_to_s(a) for a in e.args]}
    if isinstance(e, M.UnaryExpr):
        return {"kind": "unary", "op": e.op, "operand": _expr_to_s(e.operand)}
    if isinstance(e, M.BinaryExpr):
        return {"kind": "binary", "op": e.op, "left": _expr_to_s(e.left), "right": _expr_to_s(e.right)}
    raise TypeError(f"Unsupported expr: {e!r}")


def _binding_value_to_s(v) -> dict:
    if isinstance(v, M.BindingCall):
        return {"value_type": "call", "name": v.name, "args": [_binding_arg_to_s(a) for a in v.args]}
    if isinstance(v, list):
        return {"value_type": "list", "items": [_binding_value_to_s(x) for x in v]}
    if isinstance(v, bool):
        return {"value_type": "literal", "bool_value": v}
    if isinstance(v, (int, float)):
        return {"value_type": "literal", "number_value": float(v)}
    if isinstance(v, str):
        return {"value_type": "literal", "string_value": v}
    raise TypeError(f"Unsupported binding value: {v!r}")


def _binding_arg_to_s(a: M.BindingArg) -> dict:
    return {"name": a.name, "value": _binding_value_to_s(a.value)}


def _to_schema_json(s: M.Strategy) -> str:
    d = {
        "name": s.name,
        "world": [
            {"entity_kind": e.kind, "name": e.name, **{
                k: v for k, v in {
                    "side": e.properties.get("side"),
                    "role": e.properties.get("role"),
                    "under_construction": e.properties.get("under_construction"),
                    "initial": e.properties.get("initial"),
                }.items() if v is not None
            }}
            for e in s.world
        ],
        "initial": [_expr_to_s(e) for e in s.initial],
        "intent": {
            "pattern": s.intent.pattern,
            # Role bindings of a typed pattern; omitted when there are none.
            **({"pattern_bindings": dict(s.intent.pattern_bindings)} if s.intent.pattern_bindings else {}),
            "primary": _expr_to_s(s.intent.primary),
            "secondary": _expr_to_s(s.intent.secondary) if s.intent.secondary else None,
            "success": _expr_to_s(s.intent.success),
            "failure": _expr_to_s(s.intent.failure),
        },
        "derived": [{"name": d_.name, "expr": _expr_to_s(d_.expr)} for d_ in s.derived],
        "plan": {
            "start": s.plan.start,
            "nodes": [_plan_node_to_s(n) for n in s.plan.nodes],
            "transitions": [_transition_to_s(t) for t in s.plan.transitions],
        },
        "backend": s.backend,
        "bindings": [{"name": b.name, "value": _binding_value_to_s(b.value)} for b in s.bindings],
    }
    return json.dumps(d)


def _action_block_to_s(a: M.ActionBlock) -> dict:
    return {"mode": a.mode, "actions": [_expr_to_s(c) for c in a.actions]}


def _plan_node_to_s(n) -> dict:
    if isinstance(n, M.Phase):
        return {
            "node_type": "phase", "id": n.id, "purpose": n.purpose,
            "actors": n.actors, "focus": n.focus,
            "entry": _expr_to_s(n.entry) if n.entry else None,
            "actions": _action_block_to_s(n.actions) if n.actions else None,
            "invariant": _expr_to_s(n.invariant) if n.invariant else None,
            "exit": _expr_to_s(n.exit) if n.exit else None,
            "terminal": n.terminal,
            **({"repeatable": True} if n.repeatable else {}),
        }
    if isinstance(n, M.Join):
        return {"node_type": "join", "id": n.id, "policy": n.policy, "quorum": n.quorum}
    if isinstance(n, M.Place):
        return {"node_type": "place", "id": n.id, "purpose": n.purpose, "tokens": n.tokens, "capacity": n.capacity}
    raise TypeError(f"Unsupported plan node: {n!r}")


def _transition_to_s(t: M.Transition) -> dict:
    return {
        "id": t.id, "source": t.source, "target": t.target,
        "event": _expr_to_s(t.event) if t.event else None,
        "guard": _expr_to_s(t.guard) if t.guard else None,
        "actions": _action_block_to_s(t.actions) if t.actions else None,
        "priority": t.priority,
        # The v0.2 single-arc form keeps its v0.5 exchange shape.
        **({} if t.is_simple else {
            "inputs": [{"place": a.place, "weight": a.weight, "kind": a.kind} for a in t.inputs],
            "outputs": [{"place": a.place, "weight": a.weight, "kind": a.kind} for a in t.outputs],
        }),
    }
