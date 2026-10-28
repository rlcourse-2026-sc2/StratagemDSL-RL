"""Layer 6: the base-map terrain profile used to place and check point_xy."""
import pytest

from stratagemdsl import paths
from stratagemdsl.frontend import parse_file
from stratagemdsl.packaging.terrain import (RAMP, VOID, brief_coordinate_problems, check_bindings,
                                            load_profile)

pytestmark = pytest.mark.skipif(
    not paths.stormlib_path().is_file() and paths.mpqeditor_path() is None,
    reason="no StormLib build for this system; set STORMLIB_PATH or MPQEDITOR_PATH")


@pytest.fixture(scope="module")
def cerulean():
    return load_profile(paths.base_maps_dir() / "cerulean_fall_le.SC2Map")


def test_reads_size_bounds_and_levels(cerulean):
    assert (cerulean.width, cerulean.height, cerulean.bounds) == (72, 72, (0, 0, 72, 72))
    assert cerulean.cell(16.5, 18.5) == 3 and cerulean.cell(44.5, 61.5) == 2
    assert cerulean.cell(10.5, 36.5) == VOID and cerulean.cell(53.5, 44.5) == RAMP


def test_plateaus_and_ramps_describe_the_layout(cerulean):
    top = cerulean.regions[0]
    assert top.level == 3 and top.cells > 800 and top.ramps == ["R1"]
    assert len(cerulean.ramps) == 7 and all(len(r.joins) == 2 for r in cerulean.ramps)
    text = cerulean.render_context()
    assert "Playable region: x 0..72, y 0..72" in text and "R1: center" in text


def test_jctq_playable_bounds_come_from_mapinfo():
    assert load_profile(paths.base_maps_dir() / "jctq_te.SC2Map").bounds == (5, 8, 67, 64)


def test_point_checks(cerulean):
    assert cerulean.check_point(16.5, 18.5, structure_half=2.5) == []
    assert "outside the playable area" in cerulean.check_point(80, 10)[0]
    assert "void" in cerulean.check_point(10.5, 36.5)[0]
    assert "ramp" in cerulean.check_point(53.5, 45.5, structure_half=2.5)[0]
    assert cerulean.reachable((48, 56), (66, 40)) and not cerulean.reachable((10, 36), (16, 18))


def test_binding_checks(cerulean):
    ok = parse_file(paths.REPO_ROOT / "examples/demos/cerulean_lure_zerg_vs_protoss.strat", "lark")
    assert check_bindings(ok, cerulean) == []
    seed = parse_file(paths.REPO_ROOT / "tests/fixtures/seeds/dhls.strat", "lark")
    problems = check_bindings(seed, cerulean)
    assert problems and all("point_id is not portable" in p for p in problems)


@pytest.mark.parametrize("x, y, half", [(44.5, 51.5, 2.5), (53, 45, 2.5), (31, 15, 1.5), (80, 80, 0.0), (10.5, 36.5, 0.0)])
def test_nearest_valid_spot_passes_the_same_check(cerulean, x, y, half):
    fix = cerulean.nearest_valid(x, y, structure_half=half, spawn=not half)
    assert fix is not None and cerulean.check_point(*fix, structure_half=half) == []
    assert half or cerulean.spawn_ok(*fix)
    assert abs(fix[0] - min(x, 71.5)) + abs(fix[1] - min(y, 71.5)) < 12


def test_rejections_carry_a_concrete_fix(cerulean, tmp_path):
    src = (paths.REPO_ROOT / "examples/demos/cerulean_lure_zerg_vs_protoss.strat").read_text(encoding="utf-8")
    bad = tmp_path / "bad.strat"
    bad.write_text(src.replace("at=point_xy(44.5, 61.5)", "at=point_xy(44.5, 51.5)"), encoding="utf-8")
    problems = check_bindings(parse_file(bad, "lark"), cerulean)
    assert len(problems) == 1 and "spans cliff levels" in problems[0]
    assert "nearest valid spot: point_xy(" in problems[0] and "on P2, level 2" in problems[0]


def test_brief_coordinates_from_another_map_are_flagged(cerulean):
    found = brief_coordinate_problems("从 R4 坡道 (58.3, 47.7) 出发，经 (80, 12) 到 (10.5, 36.5)", cerulean)
    assert len(found) == 2 and "outside" in found[0] and "void" in found[1]
