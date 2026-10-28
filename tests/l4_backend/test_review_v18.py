"""
Regression tests for the v18-review findings U01 (P1: a literal start
phase reachable from ANOTHER start phase loses its own tail cascade,
order-dependently) and U02 (P2: the naming registry didn't cover plain
`gv_*` globals -- entities, phase active/entered flags, join count/fired,
killed_in counters -- only `gt_*` triggers).
"""

import re

from stratagemdsl.paths import compiler_root
from stratagemdsl.frontend.antlr_parser import parse_source
from stratagemdsl.backend.galaxy import lower_to_galaxy
from galaxy_mini_interp import GalaxyMiniState, run_block, extract_func_body_lines
from net_harness import Harness


COMPILER_ROOT = str(compiler_root())


def _simulate_spawn_and_init(galaxy: str) -> GalaxyMiniState:
    state = GalaxyMiniState()
    spawn = re.search(r"void gf_Spawn \(\) \{(.*?)\n\}", galaxy, re.S).group(1).split("\n")
    run_block(spawn, state)
    run_block(extract_func_body_lines(galaxy, "gt_MapInit_Func"), state)
    return state


def _start_overlap_strat(order: str) -> str:
    return f"""strategy start_overlap_test {{
  world {{
    force enemy {{ side = "enemy"; role = "test"; }}
    asset watcher {{ side = "ally"; role = "test"; }}
  }}
  initial {{ alive(enemy); alive(watcher); }}
  intent {{ pattern Test; primary alive(watcher); success alive(watcher); failure not (alive(watcher)); }}
  plan {{
    start [{order}];
    phase a {{ purpose "a"; actors [enemy]; focus [watcher]; }}
    phase b {{ purpose "b"; actors [enemy]; focus [watcher]; }}
    phase done {{ purpose "done"; actors [enemy]; focus [watcher]; do {{ hold(enemy); }} terminal success; }}
    transition a_to_b: a -> b {{ when true; priority 10; }}
    transition b_to_done: b -> done {{ when true; priority 10; }}
  }}
  binding sc2 {{
    enemy = unit_group(owner=2, unit_type="Zealot", count=2, spawn=point_id(1532430748));
    watcher = unit(owner=1, unit_type="Nexus", at=point_id(1963276538));
  }}
}}"""


def test_u01_start_phase_reachable_from_another_start_phase_still_fires_its_own_tail():
    """U01: `b` is BOTH a start phase AND reachable from `a` (also a start).
    `a`'s arrival at the already-entered once-phase `b` is discarded, `b`'s
    own token still flows to `done`, in either start order."""
    for order in ("a, b", "b, a"):
        h = Harness(_start_overlap_strat(order))
        assert h.marked == {"done"}, f"order [{order}]: tail never fired"
        assert h.vm.calls.get("UnitGroupIssueOrder", 0) == 1, f"order [{order}]: hold() ran {h.vm.calls.get('UnitGroupIssueOrder', 0)} times"


DUPLICATE_START = """strategy duplicate_start_test {
  world {
    force enemy { side = "enemy"; role = "test"; }
    asset watcher { side = "ally"; role = "test"; }
    region zone { role = "test"; }
  }
  initial { alive(enemy); alive(watcher); }
  intent { pattern Test; primary alive(watcher); success alive(watcher); failure not (alive(watcher)); }
  plan {
    start [a, a, blocked];
    phase a { purpose "a"; actors [enemy]; focus [watcher]; }
    phase blocked { purpose "blocked"; actors [enemy]; focus [watcher]; }
    join ready all;
    phase done { purpose "done"; actors [enemy]; focus [watcher]; do { hold(enemy); } terminal success; }
    transition a_ready: a -> ready { when true; priority 10; }
    transition blocked_ready: blocked -> ready { on enter(enemy, zone); priority 10; }
    transition tail: ready -> done { when true; priority 10; }
  }
  binding sc2 {
    enemy = unit_group(owner=2, unit_type="Zealot", count=2, spawn=point_id(1532430748));
    watcher = unit(owner=1, unit_type="Nexus", at=point_id(1963276538));
    zone = circle(center=point_id(1963276538), radius=8);
  }
}"""


def test_v01_lowering_also_rejects_duplicate_start_defensively():
    """Defense in depth: GalaxyLowerer itself must refuse a duplicate
    start list too, in case some caller ever hands it a Strategy that
    skipped Validator."""
    from stratagemdsl.backend.galaxy import LoweringError

    s = parse_source(DUPLICATE_START)
    try:
        lower_to_galaxy(s)
        assert False, "duplicate start should have been rejected"
    except LoweringError as e:
        assert "duplicate" in str(e).lower()
