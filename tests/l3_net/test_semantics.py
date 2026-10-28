"""Layer 3 (net): the token game -- enabling, firing, settle and dispatch rules."""
from stratagemdsl.net import TokenGame, build_net
from stratagemdsl.frontend import parse_source

from test_build import HEAD, TAIL


def game(plan: str):
    return TokenGame(build_net(parse_source(HEAD + plan + TAIL, "lark")))


def marked(g, s):
    return g.marked(s)


def step(g, s, trigger, **guards):
    return g.step(s, trigger, lambda t: guards.get(t.id, False))


EV = ("event", ("enter", (("name", "f"), ("name", "r"))))


def test_weights_read_and_inhibitor_arcs():
    g = game("""start [a]; place q { initial 1; capacity 3; } place sig { } phase a { purpose "a"; repeatable; }
    phase b { purpose "b"; }
    transition need2: a, q*2 -> b { on enter(f, r); priority 1; }
    transition add: a -> a, q { when alive(f); priority 2; }""")
    s = g.initial()
    s = step(g, s, EV)                     # need2 not enabled with one token
    assert marked(g, s) == {"a": 1, "q": 1}
    s = step(g, s, ("poll",), add=True)
    assert marked(g, s) == {"a": 1, "q": 2}
    s = step(g, s, EV)
    assert marked(g, s) == {"b": 1}


def test_capacity_blocks_and_inhibitor_waits_for_empty():
    g = game("""start [a, w]; place q { capacity 1; } phase a { purpose "a"; repeatable; } phase w { purpose "w"; }
    phase done { purpose "d"; }
    transition add: a -> a, q { when alive(f); priority 1; }
    transition gate: w, !q -> done { on enter(f, r); priority 1; }""")
    s = g.initial()
    s = step(g, s, ("poll",), add=True)
    assert marked(g, s)["q"] == 1
    x = g.ts["add"]
    assert not g.enabled(s, x) and g.capacity_blocked(s, x)
    assert step(g, s, EV) == s             # inhibited while q holds a token


def test_once_place_discards_a_second_arrival_but_the_transition_fires():
    g = game("""start [a, b]; phase a { purpose "a"; } phase b { purpose "b"; } phase m { purpose "m"; }
    transition ta: a -> m { on enter(f, r); priority 1; } transition tb: b -> m { when alive(f); priority 1; }""")
    s = step(g, g.initial(), EV)
    assert marked(g, s) == {"b": 1, "m": 1}
    s = step(g, s, ("poll",), tb=True)
    assert marked(g, s) == {"m": 1}        # b consumed, the arrival at m discarded


def test_first_wins_halts_and_clears():
    g = game("""start [a, w]; phase a { purpose "a"; } phase w { purpose "w"; }
    phase win { purpose "win"; terminal success; } phase lose { purpose "lose"; terminal failure; }
    transition ok: a -> win { on enter(f, r); priority 1; } transition ko: w -> lose { when alive(f); priority 1; }""")
    s = step(g, g.initial(), EV)
    assert s.outcome == 1 and marked(g, s) == {"win": 1}
    assert step(g, s, ("poll",), ko=True) == s


def test_settle_follows_rank_and_dispatch_uses_a_snapshot():
    g = game("""start [a]; phase a { purpose "a"; } phase b { purpose "b"; } phase c { purpose "c"; }
    phase d { purpose "d"; }
    transition hi: a -> b { when true; priority 1; } transition lo: a -> c { when true; priority 2; }
    transition next: b -> d { on enter(f, r); priority 1; }""")
    assert marked(g, g.initial()) == {"b": 1}
    g2 = game("""start [a]; phase a { purpose "a"; } phase b { purpose "b"; } phase c { purpose "c"; }
    transition first: a -> b { on enter(f, r); priority 1; } transition second: b -> c { on enter(f, r); priority 2; }""")
    s = step(g2, g2.initial(), EV, first=True, second=True)
    assert marked(g2, s) == {"b": 1}       # tokens made by this occurrence wait for the next one
    s = step(g2, s, EV, second=True)
    assert marked(g2, s) == {"c": 1}


def test_abstract_successors_cover_every_guard_combination():
    g = game("""start [a, b]; phase a { purpose "a"; } phase b { purpose "b"; } phase x { purpose "x"; } phase y { purpose "y"; }
    transition ta: a -> x { when alive(f); priority 1; } transition tb: b -> y { when alive(f); priority 1; }""")
    succ, truncated = g.successors(g.initial())
    assert not truncated
    outcomes = {tuple(sorted(g.marked(n))) for _t, _f, n, _l, _sel in succ}
    assert outcomes == {("b", "x"), ("a", "y"), ("x", "y")}
