"""Layer 3 (net): reachability-graph proofs and their diagnostics."""
from pathlib import Path

import pytest

from stratagemdsl.frontend import parse_file, parse_source
from stratagemdsl.net import analyze, build_net
from stratagemdsl.net.analysis import components
from stratagemdsl.paths import REPO_ROOT
from stratagemdsl.semantics import Validator

from test_build import HEAD, TAIL


def report(plan: str):
    return analyze(build_net(parse_source(HEAD + plan + TAIL, "lark")))


def test_dead_transition_behind_a_competing_choice():
    r = report("""start [begin]; phase begin { purpose "b"; } phase a { purpose "a"; } phase b { purpose "b"; }
    phase done { purpose "d"; terminal success; }
    transition to_a: begin -> a { when alive(f); priority 1; } transition to_b: begin -> b { on enter(f, r); priority 2; }
    transition sync: a, b -> done { when true; priority 1; }""")
    assert [t.id for t in r.dead_transitions()] == ["sync"]
    assert "done" in {p.id for p in r.never_marked()}


def test_independent_branches_are_separate_components():
    n = build_net(parse_source(HEAD + """start [a, b]; phase a { purpose "a"; } phase b { purpose "b"; }
    phase x { purpose "x"; } phase y { purpose "y"; }
    transition ta: a -> x { when alive(f); priority 1; } transition tb: b -> y { when alive(f); priority 1; }""" + TAIL, "lark"))
    assert len(components(n)) == 2
    assert analyze(n).states == 4


def test_witness_paths_reach_every_firable_transition():
    path = REPO_ROOT / "examples/learning/05_petri_feint_budget.strat"
    r = analyze(build_net(parse_file(path, "lark")))
    w = r.witnesses()
    assert set(w) == {t.id for t in r.net.transitions}
    assert [sel for _key, sel in w["go"]][-1] == ("go",)
    assert sum("again" in sel for _key, sel in w["go"]) == 2     # both budget tokens spent first


@pytest.mark.parametrize("name,code", [
    ("zeno_cycle", "N030_IMMEDIATE_CYCLE"),
    ("unbounded_counter", "N001_UNBOUNDED_PLACE"),
    ("competing_sync", "N010_DEAD_TRANSITION"),
    ("competing_sync", "N050_NO_SUCCESS_PATH"),
    ("once_cycle", "P031_CYCLE"),
])
def test_petri_negative_examples(name, code):
    s = parse_file(REPO_ROOT / "tests/fixtures/petri_negative" / f"{name}.strat", "lark")
    assert code in {d.code for d in Validator(s).validate().items}


@pytest.mark.parametrize("path", sorted((REPO_ROOT / "examples/petri").glob("*.strat"))
                         + sorted((REPO_ROOT / "examples/learning").glob("0[45]_petri_*.strat")), ids=lambda p: p.stem)
def test_petri_examples_are_clean_bounded_and_complete(path):
    v = Validator(parse_file(path, "lark"), strict_sc2=True)
    bag = v.validate()
    assert not bag.items, [str(d) for d in bag.items]
    r = v.net_report
    assert r.complete and not r.dead_transitions() and not r.never_marked()
    assert all(r.bound()[p] <= (r.net.places[p].capacity or 64) for p in r.net.places)
    assert any(r.net.places[t].terminal == "success" for t in r.terminal_reached())
