"""Layer 1: v0.6 Petri-net syntax parses identically in both frontends."""
import pytest

from stratagemdsl.core.model import Arc, Place
from stratagemdsl.frontend import parse_source
from stratagemdsl.frontend.unparse import unparse

SRC = """strategy petri_syntax {
  world { force a { side = "ally"; role = "x"; } region r { role = "x"; } }
  intent { primary alive(a); success alive(a); failure not alive(a); }
  plan {
    start [x, y];
    place budget { purpose "feints left"; initial 2; capacity 3; }
    place signal { }
    place quota { capacity 4; }
    phase x { purpose "x"; repeatable; actors [a]; }
    phase y { purpose "y"; }
    phase z { purpose "z"; terminal success; }
    transition fork: x -> y, z { on enter(a, r); priority 1; }
    transition sync: x, y, budget*2, ?signal, !quota, !budget*3 -> z, signal*2 { when tokens(budget) >= 1 and active(y); priority 2; }
    transition legacy: y -> z { when alive(a); priority 3; }
  }
}"""


@pytest.mark.parametrize("frontend", ["lark", "antlr"])
def test_places_arcs_and_repeatable(frontend):
    s = parse_source(SRC, frontend)
    nodes = {n.id: n for n in s.plan.nodes}
    assert nodes["budget"] == Place("budget", "feints left", 2, 3)
    assert nodes["signal"] == Place("signal", "", 0, None)
    assert nodes["quota"].capacity == 4 and nodes["quota"].tokens == 0
    assert nodes["x"].repeatable and not nodes["y"].repeatable
    t = {t.id: t for t in s.plan.transitions}
    assert t["fork"].outputs == [Arc("y"), Arc("z")] and t["fork"].source == "x" and t["fork"].target == "y"
    assert t["sync"].inputs == [Arc("x"), Arc("y"), Arc("budget", 2), Arc("signal", 1, "read"),
                                Arc("quota", 1, "inhibit"), Arc("budget", 3, "inhibit")]
    assert t["sync"].outputs == [Arc("z"), Arc("signal", 2)]
    assert t["legacy"].is_simple and not t["sync"].is_simple
    assert t["sync"].consumed == ["x", "y", "budget"]


def test_frontends_agree_and_unparse_round_trips():
    a, b = parse_source(SRC, "lark"), parse_source(SRC, "antlr")
    assert a.to_dict() == b.to_dict()
    again = unparse(a)
    assert parse_source(again, "lark").to_dict() == a.to_dict()
    assert parse_source(again, "antlr").to_dict() == a.to_dict()


def test_not_equal_still_lexes_next_to_inhibitor_arcs():
    src = SRC.replace("when tokens(budget) >= 1 and active(y);", "when tokens(budget) != 1;")
    for fe in ("lark", "antlr"):
        guard = next(t for t in parse_source(src, fe).plan.transitions if t.id == "sync").guard
        assert guard.op == "!="


@pytest.mark.parametrize("bad", [
    "transition t: -> y { when true; priority 1; }",           # no input arc
    "transition t: x -> { when true; priority 1; }",           # no output arc
    "transition t: x*y -> z { when true; priority 1; }",       # weight must be an integer
    "place p { initial -1; }",                                 # negative marking
    "place p { capacity 2; initial 1; }",                      # fixed field order
])
@pytest.mark.parametrize("frontend", ["lark", "antlr"])
def test_malformed_petri_syntax_is_rejected(bad, frontend):
    src = SRC.replace("    transition legacy:", f"    {bad}\n    transition legacy:")
    with pytest.raises(Exception):
        parse_source(src, frontend)


def test_new_keywords_stay_usable_as_property_names():
    src = SRC.replace('force a { side = "ally"; role = "x"; }', 'force a { side = "ally"; role = "x"; capacity = 3; place = true; }')
    for fe in ("lark", "antlr"):
        a = parse_source(src, fe).world[0]
        assert a.properties["capacity"] == 3.0 and a.properties["place"] is True


def test_empty_lists_agree_between_frontends():
    """`[]` in a name list, a property and a binding is an empty list in both frontends
    (Lark used to return [None] for the absent optional group)."""
    from stratagemdsl.frontend import antlr_parser, lark_parser
    src = ('strategy s { world { force f { tags = []; } } intent { primary true; success true; failure false; }\n'
           'plan { start []; phase a { purpose "p"; actors []; focus []; } }\n'
           'binding sc2 { f = unit_group(composition=[]); } }')
    for parser in (lark_parser, antlr_parser):
        s = parser.parse_source(src)
        assert s.plan.start == [] and s.plan.nodes[0].actors == [] and s.plan.nodes[0].focus == []
        assert s.world[0].properties == {"tags": []}
        assert s.bindings[0].value.args[0].value == []
    assert lark_parser.parse_source(src).to_dict() == antlr_parser.parse_source(src).to_dict()
