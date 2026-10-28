"""Layer 3 (net): desugaring the plan into a Strategic Petri Net."""
from stratagemdsl.frontend import parse_source
from stratagemdsl.net import EVENT, IMMEDIATE, POLLED, build_net

HEAD = """strategy s {
  world { force f { side = "ally"; role = "x"; } region r { role = "x"; } }
  intent { primary alive(f); success alive(f); failure not alive(f); }
  plan {
"""
TAIL = "  }\n  binding sc2 { f = unit_group(owner=1, unit_type=\"Marine\", count=1, spawn=point_xy(1, 1)); r = circle(center=point_xy(1, 1), radius=2); __setup__ = setup(terminal_policy=\"first_wins\"); }\n}"


def net(plan: str):
    return build_net(parse_source(HEAD + plan + TAIL, "lark"))


def test_phases_are_one_token_places_and_start_is_the_initial_marking():
    n = net("""start [a]; phase a { purpose "a"; } phase b { purpose "b"; repeatable; }
    phase c { purpose "c"; terminal success; }
    transition t: a -> b { on enter(f, r); priority 1; } transition u: b -> c { when alive(f); priority 1; }""")
    assert n.initial_marking() == {"a": 1, "b": 0, "c": 0}
    assert n.places["a"].once and not n.places["b"].once and n.places["c"].terminal == "success"
    assert all(p.capacity == 1 for p in n.places.values())
    assert n.halting


def test_all_join_becomes_per_edge_places_and_a_silent_sync():
    n = net("""start [a, b]; phase a { purpose "a"; } phase b { purpose "b"; } join j all;
    phase c { purpose "c"; terminal success; }
    transition ta: a -> j { on enter(f, r); priority 1; } transition tb: b -> j { when alive(f); priority 1; }
    transition tc: j -> c { when true; priority 1; }""")
    sync = n.transition("j.sync")
    assert sync.silent and sync.dispatch == IMMEDIATE
    assert sorted(a.place for a in sync.inputs) == ["j.in.ta", "j.in.tb"]
    assert [a.place for a in n.transition("ta").outputs] == ["j.in.ta"]
    assert [a.place for a in sync.outputs] == ["j"]


def test_quorum_join_uses_a_weighted_arc_and_a_one_shot_armed_place():
    n = net("""start [a, b, c]; phase a { purpose "a"; } phase b { purpose "b"; } phase c { purpose "c"; }
    join j atleast(2); phase d { purpose "d"; terminal success; }
    transition ta: a -> j { when true; priority 1; } transition tb: b -> j { when true; priority 1; }
    transition tc: c -> j { when true; priority 1; } transition td: j -> d { when true; priority 1; }""")
    sync = n.transition("j.sync")
    assert {(a.place, a.weight) for a in sync.inputs} == {("j.arrivals", 2), ("j.armed", 1)}
    assert n.places["j.armed"].initial == 1 and n.places["j.arrivals"].capacity == 3


def test_dispatch_classes_and_the_r03_demotion():
    n = net("""start [a]; phase a { purpose "a"; } phase b { purpose "b"; } phase c { purpose "c"; } phase d { purpose "d"; }
    place q { initial 1; }
    transition ev: a -> b { on enter(f, r); priority 5; }
    transition live: a -> c { when alive(f); priority 10; }
    transition fallback: a -> d { when true; priority 20; }
    transition marking: b, q -> c { when tokens(q) >= 1; priority 1; }""")
    kinds = {t.id: t.dispatch for t in n.transitions}
    assert kinds == {"ev": EVENT, "live": POLLED, "fallback": POLLED, "marking": IMMEDIATE}
    assert n.transition("marking").marking_guard


def test_resource_places_keep_their_declared_marking_and_capacity():
    n = net("""start [a]; place budget { initial 2; capacity 3; } phase a { purpose "a"; repeatable; }
    transition again: a, budget -> a { on enter(f, r); priority 1; }""")
    p = n.places["budget"]
    assert (p.kind, p.initial, p.capacity, p.once) == ("resource", 2, 3, False)
