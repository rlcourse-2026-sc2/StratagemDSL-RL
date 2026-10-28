"""Layer 3 (net): PNML interchange and the SNAKES cross-check of the token rules."""
from pathlib import Path

import pytest

from stratagemdsl.frontend import parse_file
from stratagemdsl.net import build_net
from stratagemdsl.net.pnml import expand_plain, from_pnml, plain_reachability, to_pnml
from stratagemdsl.paths import REPO_ROOT

SOURCES = (sorted((REPO_ROOT / "examples").glob("*/*.strat"))
           + sorted((REPO_ROOT / "tests/fixtures/corpus").glob("*.strat")))


@pytest.mark.parametrize("path", SOURCES, ids=lambda p: p.stem)
def test_pnml_round_trips_the_structure(path):
    net = build_net(parse_file(path, "lark"))
    doc = from_pnml(to_pnml(net))
    assert doc["places"] == {p.id: p.initial for p in net.places.values()}
    assert sorted(doc["transitions"]) == sorted(t.id for t in net.transitions)
    arcs = {(a.place, t.id, a.weight, a.kind) for t in net.transitions for a in t.inputs}
    arcs |= {(t.id, a.place, a.weight, "normal") for t in net.transitions for a in t.outputs}
    assert set(doc["arcs"]) == arcs


@pytest.mark.parametrize("path", SOURCES, ids=lambda p: p.stem)
def test_plain_expansion_agrees_with_snakes(path):
    pytest.importorskip("snakes")
    from stratagemdsl.net.snakes_bridge import cross_check
    r = cross_check(build_net(parse_file(path, "lark")))
    if r.skipped:
        assert path.stem == "unbounded_counter", r.skipped
        pytest.skip(r.skipped)
    assert r.ok, (r.only_ours, r.only_snakes)


def test_plain_expansion_encodes_once_with_complement_places():
    net = build_net(parse_file(REPO_ROOT / "examples/learning/02_join_and_counter.strat", "lark"))
    plain = expand_plain(net)
    assert "exploit^" in plain.places and "halt" in plain.places
    assert {t.id for t in plain.transitions if t.origin == "release"} == {"release#f", "release#s"}
    assert all(m for m in plain_reachability(plain))


def test_capacity_complement_follows_the_net_change_of_a_self_loop():
    net = build_net(parse_file(REPO_ROOT / "examples/learning/04_petri_sync_counter.strat", "lark"))
    plain = expand_plain(net)
    count = next(t for t in plain.transitions if t.origin == "count_kill")
    assert "kill_watch~" not in {a.place for a in count.inputs + count.outputs}
    assert any(dict(m).get("kills") == 2 for m in plain_reachability(plain))
