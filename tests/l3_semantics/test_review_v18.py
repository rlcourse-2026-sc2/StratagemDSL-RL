"""
Regression tests for the v18-review findings U01 (P1: a literal start
phase reachable from ANOTHER start phase loses its own tail cascade,
order-dependently) and U02 (P2: the naming registry didn't cover plain
`gv_*` globals -- entities, phase active/entered flags, join count/fired,
killed_in counters -- only `gt_*` triggers).
"""


from stratagemdsl.paths import compiler_root
from stratagemdsl.frontend.antlr_parser import parse_source


COMPILER_ROOT = str(compiler_root())

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


def test_v01_validator_rejects_duplicate_start_entries():
    """V01: `start [a, a, blocked]` has no legitimate meaning -- reject it
    explicitly instead of silently letting each repetition of `a` count as
    an independent arrival at a downstream join."""
    from stratagemdsl.semantics.validator import Validator

    s = parse_source(DUPLICATE_START)
    errors = [str(x) for x in Validator(s).validate().items if "ERROR" in str(x).upper()]
    assert any("P006_DUP_START" in e for e in errors), errors
