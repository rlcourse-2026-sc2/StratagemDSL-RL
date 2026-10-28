"""Three-valued guard evaluation over a marking.

The analysis does not know the SC2 world, so a guard is evaluated in Kleene
logic: world predicates are UNKNOWN (either outcome is possible), constants
and the marking functions ``tokens(p)`` / ``active(p)`` are exact.
"""
from __future__ import annotations

from typing import Mapping, Optional, Union

from stratagemdsl.core.model import (
    BinaryExpr, BoolExpr, CallExpr, Expr, NameExpr, NumberExpr, StringExpr, UnaryExpr,
)

UNKNOWN = None
Value = Union[bool, float, None]

MARKING_FUNCTIONS = {"tokens": "Int", "active": "Bool"}


def static_truth(expr: Optional[Expr]) -> Optional[bool]:
    """True for a missing guard or a literal ``true``, False for literal ``false``.

    Deliberately literal: v0.2 only folds `when true` / no `when`, and a
    derived name that happens to be constant is still a live condition.
    """
    if expr is None:
        return True
    if isinstance(expr, BoolExpr):
        return bool(expr.value)
    return None


def marking_refs(expr: Optional[Expr], derived: Mapping[str, Expr], _seen: frozenset = frozenset()) -> set[str]:
    """Places read by tokens()/active() in ``expr`` (derived facts expanded)."""
    out: set[str] = set()
    if expr is None:
        return out
    if isinstance(expr, CallExpr):
        if expr.name in MARKING_FUNCTIONS and expr.args and isinstance(expr.args[0], NameExpr):
            out.add(expr.args[0].name)
        for a in expr.args:
            out |= marking_refs(a, derived, _seen)
    elif isinstance(expr, UnaryExpr):
        out |= marking_refs(expr.operand, derived, _seen)
    elif isinstance(expr, BinaryExpr):
        out |= marking_refs(expr.left, derived, _seen) | marking_refs(expr.right, derived, _seen)
    elif isinstance(expr, NameExpr) and expr.name in derived and expr.name not in _seen:
        out |= marking_refs(derived[expr.name], derived, _seen | {expr.name})
    return out


def is_marking_only(expr: Optional[Expr], derived: Mapping[str, Expr], _seen: frozenset = frozenset()) -> bool:
    """The expression's value depends on nothing but constants and the marking."""
    if expr is None or isinstance(expr, (BoolExpr, NumberExpr)):
        return True
    if isinstance(expr, CallExpr):
        return (expr.name in MARKING_FUNCTIONS and len(expr.args) == 1
                and isinstance(expr.args[0], NameExpr))
    if isinstance(expr, UnaryExpr):
        return is_marking_only(expr.operand, derived, _seen)
    if isinstance(expr, BinaryExpr):
        return is_marking_only(expr.left, derived, _seen) and is_marking_only(expr.right, derived, _seen)
    if isinstance(expr, NameExpr) and expr.name in derived and expr.name not in _seen:
        return is_marking_only(derived[expr.name], derived, _seen | {expr.name})
    return False


def evaluate(expr: Optional[Expr], marking: Mapping[str, int], derived: Mapping[str, Expr],
             _seen: frozenset = frozenset()) -> Value:
    if expr is None:
        return True
    if isinstance(expr, BoolExpr):
        return bool(expr.value)
    if isinstance(expr, NumberExpr):
        return float(expr.value)
    if isinstance(expr, StringExpr):
        return UNKNOWN
    if isinstance(expr, NameExpr):
        if expr.name in derived and expr.name not in _seen:
            return evaluate(derived[expr.name], marking, derived, _seen | {expr.name})
        return UNKNOWN
    if isinstance(expr, CallExpr):
        if expr.name in MARKING_FUNCTIONS and expr.args and isinstance(expr.args[0], NameExpr):
            n = marking.get(expr.args[0].name, 0)
            return float(n) if expr.name == "tokens" else n > 0
        return UNKNOWN
    if isinstance(expr, UnaryExpr):
        v = evaluate(expr.operand, marking, derived, _seen)
        if expr.op == "not":
            return UNKNOWN if not isinstance(v, bool) else (not v)
        if expr.op == "-":
            return -v if isinstance(v, float) else UNKNOWN
        return UNKNOWN
    if isinstance(expr, BinaryExpr):
        op = expr.op
        left = evaluate(expr.left, marking, derived, _seen)
        if op in ("and", "or", "implies"):
            right = evaluate(expr.right, marking, derived, _seen)
            lb = left if isinstance(left, bool) else UNKNOWN
            rb = right if isinstance(right, bool) else UNKNOWN
            if op == "implies":
                lb = UNKNOWN if lb is UNKNOWN else (not lb)
                op = "or"
            if op == "and":
                if lb is False or rb is False:
                    return False
                return True if (lb is True and rb is True) else UNKNOWN
            if lb is True or rb is True:
                return True
            return False if (lb is False and rb is False) else UNKNOWN
        right = evaluate(expr.right, marking, derived, _seen)
        if not (isinstance(left, float) and isinstance(right, float)) or isinstance(left, bool) or isinstance(right, bool):
            if op in ("==", "!=") and isinstance(left, bool) and isinstance(right, bool):
                return (left == right) if op == "==" else (left != right)
            return UNKNOWN
        if op == "+": return left + right
        if op == "-": return left - right
        if op == "*": return left * right
        if op == "/": return UNKNOWN if right == 0 else left / right
        if op == "<": return left < right
        if op == "<=": return left <= right
        if op == ">": return left > right
        if op == ">=": return left >= right
        if op == "==": return left == right
        if op == "!=": return left != right
    return UNKNOWN


def truth(expr: Optional[Expr], marking: Mapping[str, int], derived: Mapping[str, Expr]) -> Optional[bool]:
    v = evaluate(expr, marking, derived)
    return v if isinstance(v, bool) else UNKNOWN
