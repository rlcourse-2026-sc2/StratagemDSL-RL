"""
Strategy -> StratagemDSL source unparser.

Round-trip safety policy (deliberately conservative so mutated ASTs always
re-parse identically through the ANTLR4 frontend):

- Every BinaryExpr is fully parenthesized, regardless of operator precedence.
  The grammar accepts `(expr)` anywhere an `expr` is expected, so this can
  never produce a syntax error, and it removes any need to reimplement
  precedence-aware minimal-paren printing.
- String leaves (in propertyValue / bindingExpr) are always emitted as
  quoted STRING literals. The grammar accepts STRING in every position
  that also accepts a bareword identifier, and the existing ANTLR frontend
  visitor collapses both forms to the same Python `str` after parsing -- so
  quoting is always semantically safe and needs no bareword/string
  disambiguation heuristic.
"""
from __future__ import annotations

import json
from typing import Any

from stratagemdsl.core.model import (
    Strategy, EntityDecl, Phase, Join, Place, Arc, Transition, ActionBlock, BindingCall, Expr,
    NameExpr, BoolExpr, NumberExpr, StringExpr,
    CallExpr, UnaryExpr, BinaryExpr,
)


def _num(v: float) -> str:
    f = float(v)
    if f.is_integer():
        return str(int(f))
    s = repr(f)
    if "e" in s or "E" in s:
        # repr() switches to scientific notation below ~1e-4, which the
        # NUMBER lexer rule ([0-9]+ ('.' [0-9]+)?) has no syntax for at
        # all. Expand to plain decimal via Decimal(repr(f)) -- NOT by
        # rounding to a fixed number of decimal places (that silently
        # turns a very small value like 1e-11 into 0.0, a real value
        # change, not just a formatting change). Decimal(s) parses the
        # exact decimal digits already present in repr()'s string, and
        # format(d, "f") just re-renders them without an exponent, so no
        # precision is gained or lost either way.
        from decimal import Decimal
        s = format(Decimal(s), "f")
    return s


def _quote(s: str) -> str:
    return json.dumps(s)


def _print_expr(e: Expr) -> str:
    if isinstance(e, NameExpr):
        return e.name
    if isinstance(e, BoolExpr):
        return "true" if e.value else "false"
    if isinstance(e, NumberExpr):
        return _num(e.value)
    if isinstance(e, StringExpr):
        return _quote(e.value)
    if isinstance(e, CallExpr):
        return f"{e.name}({', '.join(_print_expr(a) for a in e.args)})"
    if isinstance(e, UnaryExpr):
        return f"{e.op} ({_print_expr(e.operand)})"
    if isinstance(e, BinaryExpr):
        return f"({_print_expr(e.left)} {e.op} {_print_expr(e.right)})"
    raise TypeError(f"Unsupported expr node: {e!r}")


def _print_property_value(v: Any) -> str:
    if isinstance(v, bool):
        return "true" if v else "false"
    if isinstance(v, (int, float)):
        return _num(v)
    if isinstance(v, list):
        return "[" + ", ".join(_print_property_value(x) for x in v) + "]"
    if isinstance(v, str):
        return _quote(v)
    raise TypeError(f"Unsupported property value: {v!r}")


def _print_binding_value(v: Any) -> str:
    if isinstance(v, BindingCall):
        args = []
        for a in v.args:
            rendered = _print_binding_value(a.value)
            args.append(f"{a.name}={rendered}" if a.name else rendered)
        return f"{v.name}({', '.join(args)})"
    if isinstance(v, bool):
        return "true" if v else "false"
    if isinstance(v, (int, float)):
        return _num(v)
    if isinstance(v, list):
        return "[" + ", ".join(_print_binding_value(x) for x in v) + "]"
    if isinstance(v, str):
        return _quote(v)
    raise TypeError(f"Unsupported binding value: {v!r}")


def _print_entity(e: EntityDecl, indent: str) -> list[str]:
    lines = [f"{indent}{e.kind} {e.name} {{"]
    for k, v in e.properties.items():
        lines.append(f"{indent}  {k} = {_print_property_value(v)};")
    lines.append(f"{indent}}}")
    return lines


def _print_action_block(block: ActionBlock, indent: str) -> str:
    kw = "parallel " if block.mode == "parallel" else ""
    calls = " ".join(f"{_print_expr(a)};" for a in block.actions)
    return f"{kw}{{ {calls} }}"


def _print_phase(p: Phase, indent: str) -> list[str]:
    lines = [f"{indent}phase {p.id} {{"]
    lines.append(f'{indent}  purpose {_quote(p.purpose)};')
    if p.repeatable:
        lines.append(f"{indent}  repeatable;")
    if p.actors:
        lines.append(f"{indent}  actors [{', '.join(p.actors)}];")
    if p.focus:
        lines.append(f"{indent}  focus [{', '.join(p.focus)}];")
    if p.entry is not None:
        lines.append(f"{indent}  entry {_print_expr(p.entry)};")
    if p.actions is not None:
        lines.append(f"{indent}  do {_print_action_block(p.actions, indent)}")
    if p.invariant is not None:
        lines.append(f"{indent}  invariant {_print_expr(p.invariant)};")
    if p.exit is not None:
        lines.append(f"{indent}  exit {_print_expr(p.exit)};")
    if p.terminal is not None:
        lines.append(f"{indent}  terminal {p.terminal};")
    lines.append(f"{indent}}}")
    return lines


def _print_join(j: Join, indent: str) -> str:
    if j.policy == "atleast":
        return f"{indent}join {j.id} atleast({j.quorum});"
    return f"{indent}join {j.id} {j.policy};"


def _print_place(p: Place, indent: str) -> str:
    body = []
    if p.purpose:
        body.append(f"purpose {_quote(p.purpose)};")
    if p.tokens:
        body.append(f"initial {int(p.tokens)};")
    if p.capacity is not None:
        body.append(f"capacity {int(p.capacity)};")
    return f"{indent}place {p.id} {{ {' '.join(body)} }}" if body else f"{indent}place {p.id} {{ }}"


def print_arc(a: Arc) -> str:
    prefix = {"normal": "", "read": "?", "inhibit": "!"}[a.kind]
    return f"{prefix}{a.place}" + (f"*{int(a.weight)}" if a.weight != 1 else "")


def print_arcs(arcs: list[Arc]) -> str:
    return ", ".join(print_arc(a) for a in arcs)


def _print_transition(t: Transition, indent: str) -> list[str]:
    lines = [f"{indent}transition {t.id}: {print_arcs(t.inputs)} -> {print_arcs(t.outputs)} {{"]
    if t.event is not None:
        lines.append(f"{indent}  on {_print_expr(t.event)};")
    if t.guard is not None:
        lines.append(f"{indent}  when {_print_expr(t.guard)};")
    if t.actions is not None:
        lines.append(f"{indent}  do {_print_action_block(t.actions, indent)}")
    lines.append(f"{indent}  priority {t.priority};")
    lines.append(f"{indent}}}")
    return lines


def unparse(s: Strategy) -> str:
    lines: list[str] = [f"strategy {s.name} {{"]

    lines.append("  world {")
    for e in s.world:
        lines.extend(_print_entity(e, "    "))
    lines.append("  }")

    if s.initial:
        lines.append("  initial { " + " ".join(f"{_print_expr(e)};" for e in s.initial) + " }")

    lines.append("  intent {")
    if s.intent.pattern:
        if s.intent.pattern_bindings:
            lines.append(f"    pattern {s.intent.pattern} {{")
            for role, entity in s.intent.pattern_bindings.items():
                lines.append(f"      {role} = {entity};")
            lines.append("    }")
        else:
            lines.append(f"    pattern {s.intent.pattern};")
    lines.append(f"    primary {_print_expr(s.intent.primary)};")
    if s.intent.secondary is not None:
        lines.append(f"    secondary {_print_expr(s.intent.secondary)};")
    lines.append(f"    success {_print_expr(s.intent.success)};")
    lines.append(f"    failure {_print_expr(s.intent.failure)};")
    lines.append("  }")

    if s.derived:
        lines.append("  semantics {")
        for d in s.derived:
            lines.append(f"    derive {d.name} = {_print_expr(d.expr)};")
        lines.append("  }")

    lines.append("  plan {")
    lines.append(f"    start [{', '.join(s.plan.start)}];")
    for node in s.plan.nodes:
        if isinstance(node, Phase):
            lines.extend(_print_phase(node, "    "))
        elif isinstance(node, Join):
            lines.append(_print_join(node, "    "))
        elif isinstance(node, Place):
            lines.append(_print_place(node, "    "))
        else:
            raise TypeError(f"Unsupported plan node: {node!r}")
    for t in s.plan.transitions:
        lines.extend(_print_transition(t, "    "))
    lines.append("  }")

    if s.backend and s.bindings:
        lines.append(f"  binding {s.backend} {{")
        for b in s.bindings:
            lines.append(f"    {b.name} = {_print_binding_value(b.value)};")
        lines.append("  }")

    lines.append("}")
    return "\n".join(line for line in lines if line != "")
