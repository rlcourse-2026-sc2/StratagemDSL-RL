from __future__ import annotations
from .type import *
from .symbol import *
from lark import Lark
from enum import Enum
from pathlib import Path
import operator

GRAMMAR_FILE = r"E:\galaxy-compiler\ANSI C95_V5.lark"
parser = None

def init_judge_parser(path: str = GRAMMAR_FILE):
    global parser
    parser = Lark.open(
        path,
        parser="earley",
        ambiguity="resolve",
        propagate_positions=True,
        maybe_placeholders=False,
    )

def parse(path: str = ''):
    from .transformer import GalaxyTransformer
    transformer = GalaxyTransformer()
    _path = Path(path)
    if not _path.exists():
        err = create_error(code=1, file_path=path)
        return err
    source = _path.read_text(encoding="utf-8", errors="replace")
    cst = parser.parse(source)
    ast = transformer.transform(cst)
    return ast

BIN_OP = {
    "+": operator.add,
    "-": operator.sub,
    "*": operator.mul,
    "/": operator.truediv,
    "%": operator.mod,
    "==": operator.eq,
    "!=": operator.ne,
    "<=": operator.le,
    "<": operator.lt,
    ">": operator.gt,
    ">=": operator.ge,
    "&&": lambda a, b: a and b,
    "||": lambda a, b: a or b,
    "&": operator.and_,
    "|": operator.or_,
    "^": operator.xor,
    "<<": operator.lshift,
    ">>": operator.rshift,
}

class Status(Enum):
    OK = 1
    NOT_OK = 2
    RET = 3
    NOT_RET = 4

ERROR_DICT: dict[str, int] = {
    "UNKNOWN" :                 0,
    "FILE_NOT_FIND":            1,
    "INVALID_ARRAY_DIM":        2,
    "UNKNOWN_TYPE":             3,
    "INVALID_REF":              4,
    "VOID_VARIABLE":            5,
    "INVALID_CONST_TYPE":       6,
    "INVALID_CONST_INIT":       7,
    "INCOMPATIBLE_ASSIGN":      8,
    "INVALID_STATIC":           9,
    "GLOBAL_STRUCTREF":         10,
    "DUPLICATE_VAR_DECLARE":    11,
    "STATIC_NATIVES":           12,
    "INVALID_RETURN_TYPE":      13,
    "DUPLICATE_FUNC_DECLARE":   14,
    "MISSING_RETURN_STMT":      15,
    "INVALID_PARAM_TYPE":       16,
    "DUPLICATE_PARAM_DECLARE":  17,
    "INVALID_STRUCT_DEF":       18,
    "INVALID_FIELD_DEF":        19,
    "DUPLICATE_FIELD_DECLARE":  20,
    "INVALID_TYPEDEF":          21,
    "INVALID_COND_TYPE":        22,
    "MODIFY_CONST_VAR":         23,
    "INVALID_LVALUE":           24,
    "INCOMPATIBLE_ASSIGN_ADV":  25,
    "INVALID_FUNCTION_CALL":    26,
    "FORWARD_FUNCTION_CALL":    27,
    "ARGUEMENTS_NUM_MISMATCH":  28,
    "ARGUEMENTS_TYPE_MISMATCH": 29,
    "UNEXPECTED_RETURN_STMT":   30,
    "MISSING_RETURN_VALUE":     31,
    "INCOMPATIBLE_RETURN_TYPE": 32,
    "UNEXPECTED_BREAK_STMT":    33,
    "UNEXPECTED_CONTINUE_STMT": 34,
    "UNKNOWN_IDENTIFIER":       35,
    "INCOMPATIBLE_BINOP":       36,
    "INCOMPATIBLE_UNOP":        37,
    "VOID_FUNCTION_CALL":       38,
    "INVALID_ARRAY_ACCESS":     39,
    "INVALID_INDEX":            40,
    "INVALID_FIELD_ACCESS":     41,
    "UNKNOWN_FIELD":            42,
}