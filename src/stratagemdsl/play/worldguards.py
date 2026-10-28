"""Plan guards evaluated against a game state.

`net.guards` decides what the marking alone decides and leaves world facts
unknown. Here the same three-valued evaluation also reads a `World`: the
simulator (`play.plansim`, full knowledge) or what an agent has observed
(`PlanTracker`, fog of war). The functions follow the Galaxy lowering in
`backend.galaxy.expressions`:

    alive(X)            living members > 0          destroyed/defeated(X)  == 0
    count(X)            living members              count_in(F, R)         members inside R
    in_region(F, R)     at least one member in R    distance(A, B)         between group centres
    killed_in(F, R)     members of F that died in R targeting(A, B)        A's orders aim at B
    mission_time()      game seconds                after(t)               mission_time() >= t
    elapsed(P)          seconds since phase P was entered (in its current activation)
    tokens(P)/active(P) the marking               path_passable / center_passable: true

Anything else (or a fact the world cannot know, e.g. an enemy's target under
fog) is unknown, and an unknown guard does not fire.
"""
from __future__ import annotations

import math
from typing import Mapping, Optional, Protocol

from stratagemdsl.core.model import (BinaryExpr, BoolExpr, CallExpr, Expr, NameExpr, NumberExpr, StringExpr,
                                     UnaryExpr)

UNKNOWN = None
SUPPORTED = {"alive", "destroyed", "defeated", "count", "count_in", "in_region", "distance", "killed_in",
             "targeting", "mission_time", "after", "elapsed", "tokens", "active", "path_passable",
             "center_passable", "path_connected"}


class World(Protocol):
    def count(self, name: str) -> Optional[int]: ...
    def centroid(self, name: str) -> Optional[tuple[float, float]]: ...
    def count_in(self, name: str, region: str) -> Optional[int]: ...
    def targeting(self, a: str, b: str) -> Optional[bool]: ...
    def killed_in(self, force: str, region: str) -> Optional[int]: ...
    def seconds(self) -> float: ...
    def elapsed(self, phase: str) -> Optional[float]: ...


def _names(call: CallExpr) -> list[Optional[str]]:
    return [a.name if isinstance(a, NameExpr) else None for a in call.args]


def evaluate(expr: Optional[Expr], marking: Mapping[str, int], derived: Mapping[str, Expr], world: World,
             _seen: frozenset = frozenset()):
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
            return evaluate(derived[expr.name], marking, derived, world, _seen | {expr.name})
        return UNKNOWN
    if isinstance(expr, CallExpr):
        return _call(expr, marking, derived, world, _seen)
    if isinstance(expr, UnaryExpr):
        v = evaluate(expr.operand, marking, derived, world, _seen)
        if expr.op == "not":
            return UNKNOWN if not isinstance(v, bool) else (not v)
        if expr.op == "-":
            return -v if isinstance(v, float) else UNKNOWN
        return UNKNOWN
    if isinstance(expr, BinaryExpr):
        op = expr.op
        left = evaluate(expr.left, marking, derived, world, _seen)
        right = evaluate(expr.right, marking, derived, world, _seen)
        if op in ("and", "or", "implies"):
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
        if isinstance(left, bool) or isinstance(right, bool):
            if op in ("==", "!=") and isinstance(left, bool) and isinstance(right, bool):
                return (left == right) if op == "==" else (left != right)
            return UNKNOWN
        if not (isinstance(left, float) and isinstance(right, float)):
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


def _call(e: CallExpr, marking, derived, world: World, _seen):
    n, names = e.name, _names(e)
    if n in ("tokens", "active") and names and names[0]:
        k = marking.get(names[0], 0)
        return float(k) if n == "tokens" else k > 0
    if n in ("path_passable", "center_passable", "path_connected"):
        return True
    if n == "mission_time" and not e.args:
        return float(world.seconds())
    if n == "after" and len(e.args) == 1:
        t = evaluate(e.args[0], marking, derived, world, _seen)
        return world.seconds() >= t if isinstance(t, float) else UNKNOWN
    if n == "elapsed" and names and names[0]:
        v = world.elapsed(names[0])
        return UNKNOWN if v is None else float(v)
    if n in ("alive", "destroyed", "defeated", "count") and len(names) == 1 and names[0]:
        c = world.count(names[0])
        if c is None:
            return UNKNOWN
        if n == "alive":
            return c > 0
        if n == "count":
            return float(c)
        return c == 0
    if n in ("count_in", "in_region") and len(names) == 2 and all(names):
        c = world.count_in(names[0], names[1])
        if c is None:
            return UNKNOWN
        return float(c) if n == "count_in" else c > 0
    if n == "distance" and len(names) == 2 and all(names):
        a, b = world.centroid(names[0]), world.centroid(names[1])
        if a is None or b is None:
            return UNKNOWN
        return math.hypot(a[0] - b[0], a[1] - b[1])
    if n == "killed_in" and len(names) == 2 and all(names):
        v = world.killed_in(names[0], names[1])
        return UNKNOWN if v is None else float(v)
    if n == "targeting" and len(names) == 2 and all(names):
        return world.targeting(names[0], names[1])
    return UNKNOWN


def truth(expr: Optional[Expr], marking: Mapping[str, int], derived: Mapping[str, Expr], world: World) -> Optional[bool]:
    v = evaluate(expr, marking, derived, world)
    return v if isinstance(v, bool) else UNKNOWN


def unsupported_calls(expr: Optional[Expr], derived: Mapping[str, Expr], _seen: frozenset = frozenset()) -> set[str]:
    """Function names in a guard that this evaluator always leaves unknown."""
    out: set[str] = set()
    if expr is None:
        return out
    if isinstance(expr, CallExpr):
        if expr.name not in SUPPORTED:
            out.add(expr.name)
        for a in expr.args:
            out |= unsupported_calls(a, derived, _seen)
    elif isinstance(expr, UnaryExpr):
        out |= unsupported_calls(expr.operand, derived, _seen)
    elif isinstance(expr, BinaryExpr):
        out |= unsupported_calls(expr.left, derived, _seen) | unsupported_calls(expr.right, derived, _seen)
    elif isinstance(expr, NameExpr) and expr.name in derived and expr.name not in _seen:
        out |= unsupported_calls(derived[expr.name], derived, _seen | {expr.name})
    return out
