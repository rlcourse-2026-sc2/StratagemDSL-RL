"""Layer 1: every bundled .strat file parses, and both frontends agree.

Covers examples/ and tests/fixtures/.
"""
import pytest

from stratagemdsl.frontend import parse_file
from stratagemdsl.frontend.unparse import unparse
from stratagemdsl.frontend.lark_parser import parse_source
from stratagemdsl.paths import REPO_ROOT

SOURCES = sorted(
    p
    for d in ("examples", "tests/fixtures")
    for p in (REPO_ROOT / d).rglob("*.strat")
    if "mismatch_cases" not in p.parts
)


@pytest.mark.parametrize("path", SOURCES, ids=lambda p: p.relative_to(REPO_ROOT).as_posix())
def test_lark_and_antlr_build_the_same_ast(path):
    assert parse_file(path, "lark").to_dict() == parse_file(path, "antlr").to_dict()


@pytest.mark.parametrize("path", SOURCES[::10], ids=lambda p: p.relative_to(REPO_ROOT).as_posix())
def test_unparse_round_trips(path):
    strategy = parse_file(path, "lark")
    assert parse_source(unparse(strategy)).to_dict() == strategy.to_dict()
