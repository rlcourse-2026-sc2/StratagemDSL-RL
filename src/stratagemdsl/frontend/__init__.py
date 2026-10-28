"""Layer 1: StratagemDSL source text -> Strategy AST.

Two independent frontends build the same AST:

* ``antlr`` -- the canonical grammar (``grammar/StratagemDSL.g4``)
* ``lark``  -- a hand-mirrored LALR grammar (``grammar/StratagemDSL.lark``)

``auto`` tries ANTLR first and falls back to Lark on a syntax error.
"""
from __future__ import annotations

from pathlib import Path

from stratagemdsl.core.model import Strategy

FRONTENDS = ("auto", "antlr", "lark")


def parse_source(source: str, frontend: str = "auto") -> Strategy:
    if frontend not in FRONTENDS:
        raise ValueError(f"frontend must be one of {FRONTENDS}")
    if frontend in ("auto", "antlr"):
        from stratagemdsl.frontend import antlr_parser
        try:
            return antlr_parser.parse_source(source)
        except (RuntimeError, SyntaxError):
            if frontend == "antlr":
                raise
    from stratagemdsl.frontend import lark_parser
    return lark_parser.parse_source(source)


def parse_file(path: str | Path, frontend: str = "auto") -> Strategy:
    return parse_source(Path(path).read_text(encoding="utf-8"), frontend)


__all__ = ["FRONTENDS", "parse_file", "parse_source"]
