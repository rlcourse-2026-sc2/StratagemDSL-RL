"""The Lark and ANTLR grammars use the same names.

Contract (header of StratagemDSL.lark and StratagemDSL.g4):

* every .g4 parser rule is a Lark rule with the same name in snake_case, and
  vice versa; Lark's `start` is only the entry point and collapses to `document`;
* in a rule whose alternatives are named, every alternative is named on both
  sides, and the Lark aliases are the .g4 labels in snake_case;
* every node the Lark tree can contain has a transformer method of that name.
"""
from __future__ import annotations

import re

import pytest

pytest.importorskip("antlr4")

from stratagemdsl.frontend._generated import StratagemDSLParser as gen
from stratagemdsl.frontend.lark_parser import _T, make_parser


def snake(name: str) -> str:
    return re.sub(r"(?<!^)(?=[A-Z])", "_", name).lower()


def _lark_rules():
    """{rule: set of aliases}, without Lark's generated helper rules (`__x_star_0`)."""
    rules: dict[str, list] = {}
    for r in make_parser().rules:
        name = str(r.origin.name)
        if not name.startswith("_"):
            rules.setdefault(name, []).append(r.alias)
    return rules


def _antlr_rules():
    """{rule: set of alternative labels}, in snake_case."""
    rules = {}
    for rule in gen.StratagemDSLParser.ruleNames:
        ctx = getattr(gen.StratagemDSLParser, rule[0].upper() + rule[1:] + "Context")
        rules[snake(rule)] = {snake(c.__name__[: -len("Context")]) for c in ctx.__subclasses__()}
    return rules


def test_rule_names_correspond():
    lark = set(_lark_rules()) - {"start"}
    antlr = set(_antlr_rules())
    assert sorted(lark - antlr) == [], "Lark rules with no .g4 rule"
    assert sorted(antlr - lark) == [], ".g4 rules with no Lark rule"


def test_start_is_only_the_entry_point():
    starts = [r for r in make_parser().rules if str(r.origin.name) == "start"]
    assert len(starts) == 1
    assert [str(s.name) for s in starts[0].expansion] == ["document"]
    assert starts[0].options.expand1  # `?start`: the tree root is `document`
    assert make_parser().parse('strategy s { world { } intent { primary true; success true; '
                               'failure false; } plan { start [p]; phase p { purpose "x"; } } }'
                               ).data == "document"


def test_alternative_names_correspond():
    lark, antlr = _lark_rules(), _antlr_rules()
    for rule, aliases in lark.items():
        if rule == "start":
            continue
        named = {a for a in aliases if a is not None}
        assert not named or None not in aliases, f"{rule}: some alternatives unnamed in Lark"
        assert named == antlr[rule], f"{rule}: Lark {sorted(named)} vs .g4 {sorted(antlr[rule])}"


def test_every_lark_node_has_a_transformer_method():
    lark = _lark_rules()
    nodes = set()
    for rule, aliases in lark.items():
        if rule == "start":
            continue
        named = {a for a in aliases if a is not None}
        nodes |= named or {rule}
    missing = sorted(n for n in nodes if not callable(getattr(_T, n, None)))
    assert missing == []
