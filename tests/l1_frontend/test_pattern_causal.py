
from stratagemdsl.paths import REPO_ROOT
from stratagemdsl.frontend.lark_parser import parse_source, parse_file
from stratagemdsl.frontend.unparse import unparse


ROOT = REPO_ROOT


def test_pattern_binding_roundtrip_bootstrap():
    s = parse_file(ROOT / "tests/fixtures/seeds/sdjx.strat")
    rendered = unparse(s)
    s2 = parse_source(rendered)
    assert s2.intent.pattern == "Feint"
    assert s2.intent.pattern_bindings == s.intent.pattern_bindings
