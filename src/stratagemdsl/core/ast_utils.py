"""Small read-only helpers over the AST, shared by the checker and the backend."""
from __future__ import annotations

from stratagemdsl.core.model import BinaryExpr, BindingCall, CallExpr, UnaryExpr


def walk_calls(e):
    """Yield every CallExpr inside an expression, outermost first."""
    if e is None:
        return
    if isinstance(e, CallExpr):
        yield e
        for a in e.args:
            yield from walk_calls(a)
    elif isinstance(e, UnaryExpr):
        yield from walk_calls(e.operand)
    elif isinstance(e, BinaryExpr):
        yield from walk_calls(e.left)
        yield from walk_calls(e.right)


def binding_named(call, k, default=None):
    """Value of the named argument ``k`` of a binding call."""
    return next((a.value for a in call.args if a.name == k), default)


def binding_arg(call, k, idx, default=None):
    """Named argument ``k``, else the idx-th positional argument."""
    if not isinstance(call, BindingCall):
        return default
    v = binding_named(call, k)
    if v is not None:
        return v
    pos = [a.value for a in call.args if a.name is None]
    return pos[idx] if idx < len(pos) else default
