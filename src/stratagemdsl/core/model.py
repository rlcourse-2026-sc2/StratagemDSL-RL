from __future__ import annotations

from dataclasses import dataclass, field, asdict
from typing import Any, Optional, Union


# ----------------------------- Expressions -----------------------------

@dataclass
class Expr:
    pass


@dataclass
class NameExpr(Expr):
    name: str


@dataclass
class BoolExpr(Expr):
    value: bool


@dataclass
class NumberExpr(Expr):
    value: float


@dataclass
class StringExpr(Expr):
    value: str


@dataclass
class CallExpr(Expr):
    name: str
    args: list[Expr] = field(default_factory=list)


@dataclass
class UnaryExpr(Expr):
    op: str
    operand: Expr


@dataclass
class BinaryExpr(Expr):
    op: str
    left: Expr
    right: Expr


# ----------------------------- World -----------------------------

@dataclass
class EntityDecl:
    kind: str
    name: str
    properties: dict[str, Any] = field(default_factory=dict)


@dataclass
class Intent:
    pattern: Optional[str]
    primary: Expr
    secondary: Optional[Expr]
    success: Expr
    failure: Expr
    pattern_bindings: dict[str, str] = field(default_factory=dict)


@dataclass
class DerivedFact:
    name: str
    expr: Expr


# ----------------------------- Actions / PlanGraph -----------------------------
#
# v0.6: the plan is a Petri net. Phases, joins and `place` declarations are
# places; transitions carry explicit input/output arcs. The classic
# `transition t: a -> b` form is the single-arc special case, so `source` and
# `target` stay as the primary (first) input and output place.

@dataclass
class ActionBlock:
    mode: str = "sequence"  # sequence | parallel
    actions: list[CallExpr] = field(default_factory=list)


@dataclass
class Phase:
    id: str
    purpose: str
    actors: list[str] = field(default_factory=list)
    focus: list[str] = field(default_factory=list)
    entry: Optional[Expr] = None
    actions: Optional[ActionBlock] = None
    invariant: Optional[Expr] = None
    exit: Optional[Expr] = None
    terminal: Optional[str] = None  # success | failure
    # v0.6: a repeatable phase can be re-entered within one round (cycles).
    # The default keeps the v0.2 "enter once per round" rule: later arrivals
    # at an already-entered phase are discarded.
    repeatable: bool = False


@dataclass
class Join:
    id: str
    policy: str                  # all | any | atleast
    quorum: Optional[int] = None


@dataclass
class Place:
    """A pure token place (v0.6): budgets, counters, semaphores, signals.

    It has no actions; transitions move its tokens. ``tokens`` is the initial
    marking, ``capacity`` an optional bound (None: the analysis must prove
    the place bounded).
    """
    id: str
    purpose: str = ""
    tokens: int = 0
    capacity: Optional[int] = None


PlanNode = Union[Phase, Join, Place]

ARC_KINDS = ("normal", "read", "inhibit")


@dataclass
class Arc:
    """Arc between a place and a transition.

    normal  -- input: consume ``weight`` tokens; output: produce them
    read    -- input only (``?p``): needs ``weight`` tokens, consumes none
    inhibit -- input only (``!p``): enabled only while ``p`` holds fewer
               than ``weight`` tokens (weight 1: ``p`` is empty)
    """
    place: str
    weight: int = 1
    kind: str = "normal"


@dataclass
class Transition:
    id: str
    source: str
    target: str
    event: Optional[CallExpr]
    guard: Optional[Expr]
    actions: Optional[ActionBlock]
    priority: int
    inputs: list[Arc] = field(default_factory=list)
    outputs: list[Arc] = field(default_factory=list)

    def __post_init__(self) -> None:
        # Single-arc construction (`Transition(id, a, b, ...)`) stays valid.
        if not self.inputs and self.source:
            self.inputs = [Arc(self.source)]
        if not self.outputs and self.target:
            self.outputs = [Arc(self.target)]

    def __setattr__(self, name, value) -> None:
        # `source` / `target` name the primary arcs; code written for v0.2
        # (generators, LLM variants, tests) rewires a transition by assigning
        # them, so the primary arc follows.
        if name in ("source", "target") and "outputs" in self.__dict__:
            old = self.__dict__.get(name)
            arcs = self.inputs if name == "source" else self.outputs
            for a in arcs:
                if a.place == old and a.kind == "normal":
                    a.place = value
                    break
        object.__setattr__(self, name, value)

    @property
    def consumed(self) -> list[str]:
        """Places this transition takes tokens from (normal input arcs)."""
        return [a.place for a in self.inputs if a.kind == "normal"]

    @property
    def produced(self) -> list[str]:
        return [a.place for a in self.outputs]

    @property
    def is_simple(self) -> bool:
        """The classic one-input, one-output, weight-1 form."""
        return (len(self.inputs) == 1 and len(self.outputs) == 1
                and self.inputs[0].kind == "normal" and self.inputs[0].weight == 1
                and self.outputs[0].weight == 1)


@dataclass
class Plan:
    start: list[str]
    nodes: list[PlanNode] = field(default_factory=list)
    transitions: list[Transition] = field(default_factory=list)


# ----------------------------- Binding -----------------------------

@dataclass
class BindingArg:
    name: Optional[str]
    value: "BindingValue"


@dataclass
class BindingCall:
    name: str
    args: list[BindingArg] = field(default_factory=list)


BindingValue = Union[str, float, bool, list["BindingValue"], BindingCall]


@dataclass
class Binding:
    name: str
    value: BindingValue


# ----------------------------- Strategy -----------------------------

@dataclass
class Strategy:
    name: str
    world: list[EntityDecl]
    initial: list[Expr]
    intent: Intent
    derived: list[DerivedFact]
    plan: Plan
    backend: Optional[str]
    bindings: list[Binding]

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)
