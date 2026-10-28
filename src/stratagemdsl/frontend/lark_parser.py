"""Lark (LALR) frontend for StratagemDSL.

Mirrors ``grammar/StratagemDSL.g4``; it needs no code generation, so it is the
reference parser for debugging. Both frontends must build the same AST.

The two grammars share their names (see the header of ``StratagemDSL.lark``):
a method here is named after the Lark rule or alternative, which is the
snake_case of the .g4 rule or label that ``antlr_parser.Builder`` visits, so
``world_section`` here is ``visitWorldSection`` there.
"""
from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path

from lark import Lark, Transformer

from stratagemdsl.core.model import (
    Strategy, EntityDecl, Intent, DerivedFact, Plan, Phase, Join, Place, Arc, Transition,
    ActionBlock, Binding, BindingArg, BindingCall,
    NameExpr, BoolExpr, NumberExpr, StringExpr, CallExpr, UnaryExpr, BinaryExpr,
)


def _unquote(s: str) -> str:
    return json.loads(s)


def make_transition(tid, inputs, outputs, event, guard, actions, priority) -> Transition:
    """Shared by both frontends: the primary source/target are the first
    consumed input (falling back to the first arc) and the first output."""
    primary_in = next((a.place for a in inputs if a.kind == "normal"), inputs[0].place)
    return Transition(id=tid, source=primary_in, target=outputs[0].place, event=event, guard=guard,
                      actions=actions, priority=priority, inputs=list(inputs), outputs=list(outputs))


class _T(Transformer):
    def ID(self, t):
        return str(t)

    def soft_id(self, xs):
        return str(xs[0])

    def binding_ctor(self, xs):
        return str(xs[0])

    def INT(self, t):
        return int(t)

    def NUMBER(self, t):
        return float(t)

    def PROP_NUMBER(self, t):
        return float(t)

    def ESCAPED_STRING(self, t):
        return _unquote(str(t))

    # ---------- property values ----------
    def str_lit(self, xs): return xs[0]
    def num_lit(self, xs): return xs[0]
    def true_lit(self, _): return True
    def false_lit(self, _): return False
    def name_lit(self, xs): return xs[0]
    def list_lit(self, xs): return xs[0]
    # An empty `[]` reaches these as [None] (Lark fills the absent optional group).
    def list_value(self, xs): return [x for x in xs if x is not None]

    def property_stmt(self, xs):
        return (xs[0], xs[1])

    def entity_body(self, xs):
        return dict(xs)

    def force_decl(self, xs):
        return EntityDecl("force", xs[0], xs[1] if len(xs) > 1 else {})

    def asset_decl(self, xs):
        return EntityDecl("asset", xs[0], xs[1] if len(xs) > 1 else {})

    def region_decl(self, xs):
        return EntityDecl("region", xs[0], xs[1] if len(xs) > 1 else {})

    def route_decl(self, xs):
        return EntityDecl("route", xs[0], xs[1] if len(xs) > 1 else {})

    def world_section(self, xs):
        return ("world", list(xs))

    # ---------- expressions ----------
    # One node per precedence level, as in the .g4: a level with one child
    # passes it through; `left OP right` builds the operator node.
    def string_literal(self, xs): return StringExpr(xs[0])
    def number_literal(self, xs): return NumberExpr(xs[0])
    def true_literal(self, _): return BoolExpr(True)
    def false_literal(self, _): return BoolExpr(False)

    def atom(self, xs):
        x = xs[0]
        return NameExpr(x) if isinstance(x, str) else x

    def unary_expr(self, xs):
        if len(xs) == 1:
            return xs[0]
        return UnaryExpr("not" if xs[0].type == "NOT" else "-", xs[1])

    def _binary(self, xs):
        return xs[0] if len(xs) == 1 else BinaryExpr(str(xs[1]), xs[0], xs[2])

    product_expr = sum_expr = comparison = and_expr = or_expr = implication = _binary

    def expr(self, xs):
        return xs[0]

    def argument_list(self, xs):
        return list(xs)

    def call_expr(self, xs):
        # An absent optional argument_list arrives as None; a zero-argument
        # call must agree with the ANTLR frontend and the API registry.
        args = xs[1] if len(xs) > 1 and xs[1] is not None else []
        return CallExpr(xs[0], list(args))

    # ---------- initial / intent ----------
    def expr_stmt(self, xs):
        return xs[0]

    def initial_section(self, xs):
        return ("initial", list(xs))

    def pattern_role_binding(self, xs):
        return (xs[0], xs[1])

    def pattern_simple(self, xs):
        return ("pattern", (xs[0], {}))

    def pattern_bound(self, xs):
        return ("pattern", (xs[0], dict(xs[1:])))

    def primary_stmt(self, xs): return ("primary", xs[0])
    def secondary_stmt(self, xs): return ("secondary", xs[0])
    def success_stmt(self, xs): return ("success", xs[0])
    def failure_stmt(self, xs): return ("failure", xs[0])

    def intent_section(self, xs):
        d = dict(xs)
        pattern_spec = d.get("pattern")
        pattern_name, pattern_bindings = pattern_spec if pattern_spec else (None, {})
        return ("intent", Intent(
            pattern=pattern_name,
            primary=d["primary"],
            secondary=d.get("secondary"),
            success=d["success"],
            failure=d["failure"],
            pattern_bindings=pattern_bindings,
        ))

    # ---------- derived strategic facts ----------
    def derived_decl(self, xs):
        return DerivedFact(xs[0], xs[1])

    def semantics_section(self, xs):
        return ("semantics", list(xs))

    # ---------- plan ----------
    def start_stmt(self, xs): return ("start", xs[0])
    def plan_node(self, xs): return xs[0]

    def name_list(self, xs): return [x for x in xs if x is not None]
    def actors_stmt(self, xs): return ("actors", xs[0])
    def focus_stmt(self, xs): return ("focus", xs[0])
    def purpose_stmt(self, xs): return ("purpose", xs[0])
    def entry_stmt(self, xs): return ("entry", xs[0])
    def invariant_stmt(self, xs): return ("invariant", xs[0])
    def exit_stmt(self, xs): return ("exit", xs[0])
    def terminal_success(self, _): return "success"
    def terminal_failure(self, _): return "failure"
    def terminal_stmt(self, xs): return ("terminal", xs[0])
    def repeatable_stmt(self, _): return ("repeatable", True)

    def action_stmt(self, xs): return xs[0]
    def sequential_block(self, xs): return ActionBlock("sequence", list(xs))
    def parallel_block(self, xs): return ActionBlock("parallel", list(xs))
    def do_stmt(self, xs): return ("do", xs[0])

    def phase_decl(self, xs):
        pid = xs[0]
        d = {}
        for item in xs[1:]:
            if isinstance(item, tuple):
                d[item[0]] = item[1]
        return Phase(
            id=pid,
            purpose=d["purpose"],
            actors=d.get("actors", []),
            focus=d.get("focus", []),
            entry=d.get("entry"),
            actions=d.get("do"),
            invariant=d.get("invariant"),
            exit=d.get("exit"),
            terminal=d.get("terminal"),
            repeatable=d.get("repeatable", False),
        )

    # ---------- v0.6 places and arcs ----------
    def place_tokens_stmt(self, xs): return ("tokens", int(xs[0]))
    def capacity_stmt(self, xs): return ("capacity", int(xs[0]))

    def place_decl(self, xs):
        d = dict(x for x in xs[1:] if isinstance(x, tuple))
        return Place(xs[0], d.get("purpose", ""), d.get("tokens", 0), d.get("capacity"))

    def arc_normal(self, xs): return Arc(xs[0])
    def arc_weighted(self, xs): return Arc(xs[0], int(xs[1]))
    def arc_read(self, xs): return Arc(xs[0], 1, "read")
    def arc_read_weighted(self, xs): return Arc(xs[0], int(xs[1]), "read")
    def arc_inhibit(self, xs): return Arc(xs[0], 1, "inhibit")
    def arc_inhibit_weighted(self, xs): return Arc(xs[0], int(xs[1]), "inhibit")
    def arc_list(self, xs): return list(xs)

    def join_all(self, _): return ("all", None)
    def join_any(self, _): return ("any", None)
    def join_atleast(self, xs): return ("atleast", xs[0])

    def join_decl(self, xs):
        jid = xs[0]
        policy, quorum = xs[1]
        return Join(jid, policy, quorum)

    def on_stmt(self, xs): return ("on", xs[0])
    def when_stmt(self, xs): return ("when", xs[0])

    def transition_decl(self, xs):
        tid, inputs, outputs = xs[0], xs[1], xs[2]
        priority = xs[-1]
        d = {}
        for item in xs[3:-1]:
            if isinstance(item, tuple):
                d[item[0]] = item[1]
        return make_transition(tid, inputs, outputs, d.get("on"), d.get("when"), d.get("do"), int(priority))

    def plan_section(self, xs):
        start = None
        nodes = []
        transitions = []
        for x in xs:
            if isinstance(x, tuple) and x[0] == "start":
                start = x[1]
            elif isinstance(x, Transition):
                transitions.append(x)
            elif isinstance(x, (Phase, Join, Place)):
                nodes.append(x)
        return ("plan", Plan(start=start, nodes=nodes, transitions=transitions))

    # ---------- binding ----------
    def binding_string(self, xs): return xs[0]
    def binding_number(self, xs): return xs[0]
    def binding_true(self, _): return True
    def binding_false(self, _): return False
    def binding_name(self, xs): return xs[0]
    def binding_list(self, xs): return [x for x in xs if x is not None]

    def named_binding_arg(self, xs):
        return BindingArg(xs[0], xs[1])

    def positional_binding_arg(self, xs):
        return BindingArg(None, xs[0])

    def binding_arg_list(self, xs):
        return list(xs)

    def binding_call(self, xs):
        name = xs[0]
        args = xs[1] if len(xs) > 1 and isinstance(xs[1], list) else []
        return BindingCall(name, list(args))

    def binding_stmt(self, xs):
        return Binding(xs[0], xs[1])

    def binding_section(self, xs):
        backend = xs[0]
        bindings = [x for x in xs[1:] if isinstance(x, Binding)]
        return ("binding", (backend, bindings))

    # ---------- strategy ----------
    def strategy_decl(self, xs):
        name = xs[0]
        world = []
        initial = []
        intent = None
        derived = []
        plan = None
        backend = None
        bindings = []

        for x in xs[1:]:
            if not isinstance(x, tuple):
                continue
            tag = x[0]
            if tag == "world":
                world = x[1]
            elif tag == "initial":
                initial = x[1]
            elif tag == "intent":
                intent = x[1]
            elif tag == "semantics":
                derived = x[1]
            elif tag == "plan":
                plan = x[1]
            elif tag == "binding":
                backend, bindings = x[1]

        return Strategy(name, world, initial, intent, derived, plan, backend, bindings)

    def document(self, xs):
        return xs[0]


@lru_cache(maxsize=1)
def make_parser() -> Lark:
    grammar_path = Path(__file__).parent / "grammar" / "StratagemDSL.lark"
    return Lark(grammar_path.read_text(encoding="utf-8"), parser="lalr", start="start")


def parse_tree(source: str):
    """Lark parse tree, before it is transformed into a Strategy."""
    return make_parser().parse(source)


def parse_source(source: str) -> Strategy:
    tree = parse_tree(source)
    result = _T().transform(tree)
    if not isinstance(result, Strategy):
        raise TypeError(f"Expected Strategy, got {type(result)!r}")
    return result


def parse_file(path: str | Path) -> Strategy:
    return parse_source(Path(path).read_text(encoding="utf-8"))
