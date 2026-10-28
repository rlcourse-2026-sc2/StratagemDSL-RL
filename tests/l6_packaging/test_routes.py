"""Layer 6 view: movement routes of the plan over the base map's terrain (`strat route`)."""
import copy
import json
import math

import pytest

from stratagemdsl import cli, paths, pipeline
from stratagemdsl.frontend import parse_file, parse_source
from stratagemdsl.packaging.terrain import RAMP, VOID, load_profile
from stratagemdsl.views.routes import guess_base_map, plan_legs, plan_routes, write_routes

pytestmark = pytest.mark.skipif(
    not paths.stormlib_path().is_file() and paths.mpqeditor_path() is None,
    reason="no StormLib build for this system; set STORMLIB_PATH or MPQEDITOR_PATH")

ROOT = paths.base_maps_dir().parents[1]
CERULEAN_SRC = ROOT / "examples/petri/cerulean_feint_cycle.strat"
SDJX_SRC = ROOT / "examples/petri/sdjx_feint_cycle.strat"


@pytest.fixture(scope="module")
def cerulean():
    return load_profile(paths.base_maps_dir() / "cerulean_fall_le.SC2Map")


@pytest.fixture(scope="module")
def feint():
    return parse_file(CERULEAN_SRC)


def _leg(plan, force, origin, target):
    return next(l for l in plan.legs if (l.force, l.origin, l.target) == (force, origin, target))


def test_legs_follow_the_plan_graph_including_the_cycle(feint):
    forces = [e.name for e in feint.world if e.kind in ("force", "asset")]
    legs = {(f, o, t) for f, _ctx, _a, o, t in plan_legs(feint, forces)}
    assert legs == {
        ("feint_force", "spawn:feint_force", "main_threat_zone"),
        ("feint_force", "staging_zone", "main_threat_zone"),       # second round of the feint cycle
        ("feint_force", "main_threat_zone", "staging_zone"),
        ("main_force", "spawn:main_force", "enemy_expansion"),
        ("defenders", "spawn:defenders", "enemy_main"),
    }


def test_cerulean_ground_paths_respect_cliffs_and_ramps(feint, cerulean):
    plan = plan_routes(feint, cerulean)
    assert {l.status for l in plan.legs} == {"ok"} and plan.warnings == []
    first = _leg(plan, "feint_force", "spawn:feint_force", "main_threat_zone")
    assert first.ramps[0] == "R1" and first.plateaus[0] == "P1" and first.plateaus[-1] == "P2"
    assert _leg(plan, "feint_force", "main_threat_zone", "staging_zone").ramps == ["R5"]
    blocked = {(int(x), int(y)) for x, y, _ in cerulean.blockers}
    for leg in plan.legs:
        cells = [(int(x), int(y)) for x, y in leg.path[1:]]
        for a, b in zip(cells, cells[1:]):
            la, lb = cerulean.level[a[1]][a[0]], cerulean.level[b[1]][b[0]]
            assert max(abs(a[0] - b[0]), abs(a[1] - b[1])) == 1
            assert la != VOID and lb != VOID and (la == lb or RAMP in (la, lb))
            assert b not in blocked
        target = plan.locations[leg.target]
        end = leg.path[-1]
        reach = target.radius if target.kind == "region" else target.footprint + 1.5
        assert math.hypot(end[0] - target.x, end[1] - target.y) <= reach + 0.01


def test_a_cut_map_reports_unreachable(feint, cerulean):
    cut = copy.deepcopy(cerulean)
    for row in cut.level:
        row[36] = VOID
    plan = plan_routes(feint, cut)
    leg = _leg(plan, "feint_force", "spawn:feint_force", "main_threat_zone")
    assert leg.status == "unreachable" and leg.path == []
    assert any("no ground path" in w for w in plan.warnings)


def test_air_units_fly_straight_and_point_ids_resolve():
    sdjx = load_profile(paths.base_maps_dir() / "sdjx_te.SC2Map")
    plan = plan_routes(parse_file(SDJX_SRC), sdjx)
    medivacs = [l for l in plan.legs if l.force == "feint_force"]
    assert medivacs and all(l.status == "air" and len(l.path) == 2 for l in medivacs)
    assert plan.locations["enemy_main"].x == pytest.approx(54.99, abs=0.01)
    assert {l.status for l in plan.legs if l.force != "feint_force"} == {"ok"}


def test_missing_coordinates_are_reported(feint, cerulean):
    text = CERULEAN_SRC.read_text(encoding="utf-8").replace("spawn=point_xy(14, 25)", "spawn=point_id(1)")
    plan = plan_routes(parse_source(text), cerulean)
    assert _leg(plan, "feint_force", "spawn:feint_force", "main_threat_zone").status == "no_position"


def test_write_routes_and_guess_base_map(feint, tmp_path):
    assert guess_base_map(CERULEAN_SRC, paths.base_maps_dir()).name == "cerulean_fall_le.SC2Map"
    assert guess_base_map(SDJX_SRC, paths.base_maps_dir()).name == "sdjx_te.SC2Map"
    plan, files = write_routes(feint, paths.base_maps_dir() / "cerulean_fall_le.SC2Map", tmp_path, "x", png=False)
    assert files == ["x.routes.json", "x.routes.svg"]
    data = json.loads((tmp_path / "x.routes.json").read_text(encoding="utf-8"))
    assert data["format"] == "stratagemdsl.routes.v1" and len(data["legs"]) == len(plan.legs)
    assert (tmp_path / "x.routes.svg").read_text(encoding="utf-8").startswith("<svg")


def test_cli_route_and_pack_artifacts(tmp_path, capsys):
    assert cli.main(["route", str(CERULEAN_SRC), "-o", str(tmp_path), "--no-png", "--strict"]) == 0
    assert "spawn feint_force -> main_threat_zone" in capsys.readouterr().out
    # write_artifacts adds the routes whenever the run knows its base map (set by the pack stage)
    r = pipeline.run(CERULEAN_SRC, until="check", out_dir=tmp_path / "run")
    r.base_map = paths.base_maps_dir() / "cerulean_fall_le.SC2Map"
    pipeline.write_artifacts(r, tmp_path / "run")
    summary = json.loads((tmp_path / "run" / "result.json").read_text(encoding="utf-8"))
    assert summary["routes"]["status"] == {"ok": 5}
    assert (tmp_path / "run" / "cerulean_feint_cycle.routes.svg").is_file()


def test_arid_besiege_wei_ambush_sits_on_the_way_home():
    """围魏救赵 on Arid Plateau: the recalled siege army's ground path crosses Guiling,
    and "attack the siege force" resolves to where the `on enter` event saw it."""
    src = ROOT / "examples/petri/arid_besiege_wei.strat"
    assert guess_base_map(src, paths.base_maps_dir()).name == "arid_plateau.SC2Map"
    plan = plan_routes(parse_file(src), load_profile(paths.base_maps_dir() / "arid_plateau.SC2Map"))
    home = _leg(plan, "siege_force", "besieged_base", "enemy_home_zone")
    assert home.status == "ok" and home.ramps == ["R1", "R2"] and home.plateaus == ["P1", "P4", "P5"]
    zone = plan.locations["ambush_zone"]
    assert any(math.hypot(x - zone.x, y - zone.y) <= zone.radius for x, y in home.path)
    assert _leg(plan, "raid_force", "enemy_home", "ambush_zone").status == "ok"
    assert {(l.force, l.target) for l in plan.legs if l.status != "already_there"} == {
        ("siege_force", "besieged_base"), ("siege_force", "enemy_home_zone"), ("raid_force", "enemy_home_zone"),
        ("raid_force", "ambush_zone"), ("ambush_force", "ambush_zone")}
