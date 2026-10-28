"""A small Galaxy interpreter for the code StratagemDSL generates.

Parses MapScript.galaxy with a Lark grammar of the Galaxy subset the backend
emits (globals, functions, locals, if/while/break/continue/return, the usual
operators) and executes it against a dictionary of globals. Natives are
stubbed: a call to an undefined function returns an opaque value whose
comparisons are false, unless a test registers an implementation in
`natives`. That is enough to run the plan's token game -- marking counters,
enabling functions, firing functions, the settle loop and the dispatch
triggers -- which never depends on native results once world guards are
replaced by oracle globals (`GalaxyLowerer(..., guard_oracle=True)`).

This is a test instrument, not a game simulator.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from functools import lru_cache
from typing import Any, Callable, Optional

from lark import Lark, Token, Tree

GRAMMAR = r"""
start: item*
?item: include | global_decl | func_def | func_proto
include: "include" STRING
global_decl: type NAME ("=" expr)? ";"
func_proto: type NAME "(" [params] ")" ";"
func_def: type NAME "(" [params] ")" block
params: param ("," param)*
param: type NAME
type: NAME
block: "{" stmt* "}"
?stmt: block
     | local_decl
     | "if" "(" expr ")" block ["else" (block | if_only)]   -> if_stmt
     | "while" "(" expr ")" block                           -> while_stmt
     | "break" ";"                                          -> break_stmt
     | "continue" ";"                                       -> continue_stmt
     | "return" [expr] ";"                                  -> return_stmt
     | NAME ASSIGN_OP expr ";"                              -> assign
     | expr ";"                                             -> expr_stmt
if_only: "if" "(" expr ")" block ["else" (block | if_only)]
local_decl: type NAME ("=" expr)? ";"
ASSIGN_OP.2: "+=" | "-=" | "*=" | "/=" | "="
?expr: or_e
?or_e: and_e | or_e "||" and_e        -> or_op
?and_e: bor_e | and_e "&&" bor_e      -> and_op
?bor_e: bxor_e | bor_e "|" bxor_e     -> bor
?bxor_e: band_e | bxor_e "^" band_e   -> bxor
?band_e: eq_e | band_e "&" eq_e       -> band
?eq_e: rel_e | eq_e EQOP rel_e        -> binop
?rel_e: shift_e | rel_e RELOP shift_e -> binop
?shift_e: add_e | shift_e SHIFTOP add_e -> binop
?add_e: mul_e | add_e ADDOP mul_e     -> binop
?mul_e: unary | mul_e MULOP unary     -> binop
?unary: "!" unary                     -> not_op
      | "-" unary                     -> neg_op
      | "~" unary                     -> inv_op
      | atom
?atom: NUMBER                         -> number
     | STRING                         -> string
     | "true"                         -> true
     | "false"                        -> false
     | "null"                         -> null
     | NAME "(" [args] ")"            -> call
     | NAME                           -> var
     | "(" expr ")"
args: expr ("," expr)*
EQOP.3: "==" | "!="
RELOP: "<=" | ">=" | "<" | ">"
SHIFTOP.3: "<<" | ">>"
ADDOP: "+" | "-"
MULOP: "*" | "/" | "%"
NAME: /(?!(if|else|while|break|continue|return|true|false|null|include)\b)[A-Za-z_][A-Za-z0-9_]*/
NUMBER: /[0-9]+(\.[0-9]+)?/
STRING: /"(\\.|[^"\\])*"/
%ignore /\s+/
%ignore /\/\/[^\n]*/
"""


class Opaque:
    """Result of a stubbed native: never equal, never true, absorbs arithmetic."""
    def __repr__(self):
        return "<native>"


OPAQUE = Opaque()
DEFAULTS = {"int": 0, "fixed": 0.0, "bool": False, "string": ""}


class _Break(Exception):
    pass


class _Continue(Exception):
    pass


class _Return(Exception):
    def __init__(self, value):
        self.value = value


class OperationLimit(RuntimeError):
    pass


@lru_cache(maxsize=1)
def parser() -> Lark:
    return Lark(GRAMMAR, parser="lalr", maybe_placeholders=True)


@dataclass
class GalaxyVM:
    source: str
    globals: dict[str, Any] = field(default_factory=dict)
    natives: dict[str, Callable[..., Any]] = field(default_factory=dict)
    calls: dict[str, int] = field(default_factory=dict)
    op_limit: int = 2_000_000

    def __post_init__(self):
        tree = parser().parse(self.source)
        self.functions: dict[str, Tree] = {}
        self.types: dict[str, str] = {}
        self._ops = 0
        for item in tree.children:
            if item.data == "global_decl":
                ty, name = str(item.children[0].children[0]), str(item.children[1])
                self.types[name] = ty
                self.globals[name] = DEFAULTS.get(ty, None)
            elif item.data == "func_def":
                self.functions[str(item.children[1])] = item

    # ------------------------------------------------------------ calls
    def call(self, name: str, *args):
        self._ops = 0
        return self._call(name, list(args))

    def _call(self, name: str, args: list):
        self.calls[name] = self.calls.get(name, 0) + 1
        fn = self.functions.get(name)
        if fn is None:
            impl = self.natives.get(name)
            return impl(*args) if impl else OPAQUE
        params = fn.children[2]
        frame: dict[str, Any] = {}
        if params is not None:
            for p, v in zip(params.children, args):
                frame[str(p.children[1])] = v
        try:
            self._block(fn.children[3], frame)
        except _Return as r:
            return r.value
        return None

    # ------------------------------------------------------- statements
    def _block(self, block: Tree, frame: dict):
        for st in block.children:
            self._stmt(st, frame)

    def _stmt(self, st: Tree, frame: dict):
        self._ops += 1
        if self._ops > self.op_limit:
            raise OperationLimit("Galaxy execution exceeded the operation limit")
        k = st.data
        if k == "block":
            self._block(st, frame)
        elif k == "local_decl":
            ty, name = str(st.children[0].children[0]), str(st.children[1])
            frame[name] = self._expr(st.children[2], frame) if len(st.children) > 2 and st.children[2] is not None \
                else DEFAULTS.get(ty, None)
        elif k in ("if_stmt", "if_only"):
            cond, then, other = st.children
            if self._truth(self._expr(cond, frame)):
                self._block(then, frame)
            elif other is not None:
                self._stmt(other, frame) if other.data == "if_only" else self._block(other, frame)
        elif k == "while_stmt":
            cond, body = st.children
            while self._truth(self._expr(cond, frame)):
                self._ops += 1
                if self._ops > self.op_limit:
                    raise OperationLimit("Galaxy loop exceeded the operation limit")
                try:
                    self._block(body, frame)
                except _Break:
                    break
                except _Continue:
                    continue
        elif k == "break_stmt":
            raise _Break()
        elif k == "continue_stmt":
            raise _Continue()
        elif k == "return_stmt":
            raise _Return(self._expr(st.children[0], frame) if st.children[0] is not None else None)
        elif k == "assign":
            name, op, value = str(st.children[0]), str(st.children[1]), self._expr(st.children[2], frame)
            scope = frame if name in frame else self.globals
            if op != "=":
                value = self._arith(op[0], scope.get(name), value)
            scope[name] = value
        elif k == "expr_stmt":
            self._expr(st.children[0], frame)
        else:
            raise NotImplementedError(k)

    # ------------------------------------------------------ expressions
    @staticmethod
    def _truth(v) -> bool:
        return v is True or (isinstance(v, (int, float)) and not isinstance(v, bool) and v != 0)

    @staticmethod
    def _arith(op: str, a, b):
        if isinstance(a, Opaque) or isinstance(b, Opaque) or a is None or b is None:
            return OPAQUE
        if isinstance(a, str) or isinstance(b, str):
            return OPAQUE if op != "+" else str(a) + str(b)
        if op == "+": return a + b
        if op == "-": return a - b
        if op == "*": return a * b
        if op == "/":
            if b == 0:
                return OPAQUE
            return a // b if isinstance(a, int) and isinstance(b, int) else a / b
        if op == "%": return a % b if b else OPAQUE
        raise NotImplementedError(op)

    def _expr(self, e, frame: dict):
        if isinstance(e, Token):
            raise NotImplementedError(e)
        k = e.data
        if k == "number":
            t = str(e.children[0])
            return float(t) if "." in t else int(t)
        if k == "string":
            return str(e.children[0])[1:-1]
        if k == "true":
            return True
        if k == "false":
            return False
        if k == "null":
            return None
        if k == "var":
            name = str(e.children[0])
            if name in frame:
                return frame[name]
            if name in self.globals:
                return self.globals[name]
            return OPAQUE      # engine constants (c_*), presets
        if k == "call":
            name = str(e.children[0])
            args = [self._expr(a, frame) for a in (e.children[1].children if e.children[1] is not None else [])]
            return self._call(name, args)
        if k == "not_op":
            v = self._expr(e.children[0], frame)
            return False if isinstance(v, Opaque) else not self._truth(v)
        if k == "neg_op":
            v = self._expr(e.children[0], frame)
            return -v if isinstance(v, (int, float)) and not isinstance(v, bool) else OPAQUE
        if k == "inv_op":
            v = self._expr(e.children[0], frame)
            return ~v if isinstance(v, int) else OPAQUE
        if k == "and_op":
            return self._truth(self._expr(e.children[0], frame)) and self._truth(self._expr(e.children[1], frame))
        if k == "or_op":
            return self._truth(self._expr(e.children[0], frame)) or self._truth(self._expr(e.children[1], frame))
        if k in ("bor", "bxor", "band"):
            a, b = self._expr(e.children[0], frame), self._expr(e.children[1], frame)
            if not (isinstance(a, int) and isinstance(b, int)):
                return OPAQUE
            return a | b if k == "bor" else a ^ b if k == "bxor" else a & b
        if k == "binop":
            a, op, b = self._expr(e.children[0], frame), str(e.children[1]), self._expr(e.children[2], frame)
            if op in ("==", "!="):
                if isinstance(a, Opaque) or isinstance(b, Opaque):
                    return False
                return (a == b) if op == "==" else (a != b)
            if op in ("<", "<=", ">", ">="):
                if not (isinstance(a, (int, float)) and isinstance(b, (int, float))):
                    return False
                return {"<": a < b, "<=": a <= b, ">": a > b, ">=": a >= b}[op]
            if op in ("<<", ">>"):
                if not (isinstance(a, int) and isinstance(b, int)):
                    return OPAQUE
                return a << b if op == "<<" else a >> b
            return self._arith(op, a, b)
        raise NotImplementedError(k)

    # ------------------------------------------------------ map lifecycle
    def boot(self) -> None:
        """InitGlobals + the MapInit trigger body (spawn, setup, start actions, settle)."""
        self.call("InitGlobals")
        self.call("gt_MapInit_Func", False, True)

    def run_trigger(self, trigger: str, *, test_conds: bool = False) -> Any:
        return self.call(f"{trigger}_Func", test_conds, True)
