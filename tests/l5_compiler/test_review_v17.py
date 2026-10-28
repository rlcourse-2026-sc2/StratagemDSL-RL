"""
Regression tests for the v17-review findings T01 (P1: same incoming edge
double-counted when a plain phase is reachable via two distinct static
paths within one synchronous pass) and T02 (P2: name-collision avoidance
gaps beyond the original S04 case -- reserved MapInit/Reset names, cross
variable/function-name collisions, and ambiguous counter-name
concatenation).
"""

import re
import tempfile
from pathlib import Path

from stratagemdsl.paths import compiler_root
from stratagemdsl.frontend.antlr_parser import parse_source
from stratagemdsl.semantics.validator import Validator
from stratagemdsl.backend.galaxy import GalaxyLowerer
from stratagemdsl.compiler.galaxycc_adapter import compile_galaxy_source


COMPILER_ROOT = str(compiler_root())

JOIN_DUPLICATE_ARRIVAL = """strategy join_duplicate_arrival_test {
  world {
    force enemy { side = "enemy"; role = "test"; }
    asset watcher { side = "ally"; role = "test"; }
    region zone { role = "test"; }
  }
  initial { alive(enemy); alive(watcher); }
  intent { pattern Test; primary alive(watcher); success alive(watcher); failure not (alive(watcher)); }
  plan {
    start [a, b, blocked];
    phase a { purpose "a"; actors [enemy]; focus [watcher]; }
    phase b { purpose "b"; actors [enemy]; focus [watcher]; }
    phase blocked { purpose "blocked"; actors [enemy]; focus [watcher]; }
    join pass any;
    phase middle { purpose "middle"; actors [enemy]; focus [watcher]; }
    join ready all;
    phase done { purpose "done"; actors [enemy]; focus [watcher]; do { hold(enemy); } terminal success; }
    transition a_to_middle: a -> middle { when true; priority 10; }
    transition b_to_pass: b -> pass { when true; priority 10; }
    transition pass_to_middle: pass -> middle { when true; priority 10; }
    transition middle_ready: middle -> ready { when true; priority 10; }
    transition blocked_ready: blocked -> ready { on enter(enemy, zone); priority 10; }
    transition tail: ready -> done { when true; priority 10; }
  }
  binding sc2 {
    enemy = unit_group(owner=2, unit_type="Zealot", count=2, spawn=point_id(1532430748));
    watcher = unit(owner=1, unit_type="Nexus", at=point_id(1963276538));
    zone = circle(center=point_id(1963276538), radius=8);
  }
}"""


def _strat_with_transition_named(name: str) -> str:
    # U03 fix: uses a real `on` event (not an eventless `when count(...)`
    # guard), so this transition is lowered through the SAME single-
    # transition event-trigger path (`gt_{_safe(id)}`) that a legally
    # user-named MapInit/Reset transition would actually collide on. The
    # eventless form instead routes through the per-SOURCE combined poll
    # dispatcher (`gt_poll_<source>`), which never even attempts the name
    # this test exists to check -- exercising it gave a false sense of
    # coverage without ever touching the target collision.
    return f"""strategy name_reserved_test {{
  world {{
    force f {{ side = "ally"; role = "test"; }}
    region zone {{ role = "test"; }}
  }}
  initial {{ alive(f); }}
  intent {{ pattern Test; primary alive(f); success alive(f); failure not (alive(f)); }}
  plan {{
    start [begin];
    phase begin {{ purpose "b"; actors [f]; focus [f]; }}
    phase done {{ purpose "d"; actors [f]; focus [f]; terminal success; }}
    transition {name}: begin -> done {{ on enter(f, zone); priority 10; }}
  }}
  binding sc2 {{
    f = unit_group(owner=1, unit_type="Zealot", count=3, spawn=point_id(1532430748));
    zone = circle(center=point_id(1532430748), radius=5);
  }}
}}"""


def _assert_no_dup_names_and_compiles(strat_text: str, transition_id: str | None = None):
    s = parse_source(strat_text)
    assert not [x for x in Validator(s).validate().items if "ERROR" in str(x).upper()]
    lowerer = GalaxyLowerer(s)
    galaxy = lowerer.emit()
    if transition_id is not None:
        # Confirms this test is actually exercising the event-trigger
        # naming path it claims to, not silently degrading to the
        # eventless poll-dispatcher path (U03).
        assert lowerer.transition_kinds[transition_id]["kind"] == "event", (
            f"expected transition '{transition_id}' to lower through the single-transition "
            f"event-trigger path, but it did not -- this test would not actually exercise the "
            f"naming collision it's meant to check"
        )
    var_names = re.findall(r"trigger (gt_\w+);", galaxy)
    func_names = re.findall(r"bool (gt_\w+) \(bool testConds", galaxy)
    int_names = re.findall(r"int (gv_\w+);", galaxy)
    combined = var_names + func_names
    assert len(combined) == len(set(combined)), f"duplicate trigger/function names: {combined}"
    assert len(int_names) == len(set(int_names)), f"duplicate int global names: {int_names}"
    with tempfile.TemporaryDirectory() as tmp:
        result = compile_galaxy_source(galaxy, compiler_root=COMPILER_ROOT, source_path=str(Path(tmp) / "t.galaxy"))
    assert result.judge_ok, result.judge_result


def test_t02_transition_named_mapinit_does_not_collide_with_the_fixed_mapinit_trigger():
    _assert_no_dup_names_and_compiles(_strat_with_transition_named("MapInit"), transition_id="MapInit")


def test_t02_transition_named_reset_does_not_collide_with_the_fixed_reset_trigger():
    _assert_no_dup_names_and_compiles(_strat_with_transition_named("Reset"), transition_id="Reset")


NAME_FUNCTION_CROSS_KIND = """strategy name_function_cross_kind_test {
  world {
    force f { side = "ally"; role = "test"; }
    force g { side = "ally"; role = "test"; }
    region zone_f { role = "test"; }
    region zone_g { role = "test"; }
  }
  initial { alive(f); alive(g); }
  intent { pattern Test; primary alive(f); success alive(f); failure not (alive(f)); }
  plan {
    start [begin1, begin2];
    phase begin1 { purpose "b1"; actors [f]; focus [f]; }
    phase begin2 { purpose "b2"; actors [g]; focus [g]; }
    phase done1 { purpose "d1"; actors [f]; focus [f]; terminal success; }
    phase done2 { purpose "d2"; actors [g]; focus [g]; terminal success; }
    transition hit: begin1 -> done1 { on enter(f, zone_f); priority 10; }
    transition hit_Func: begin2 -> done2 { on enter(g, zone_g); priority 10; }
  }
  binding sc2 {
    f = unit_group(owner=1, unit_type="Zealot", count=3, spawn=point_id(1532430748));
    g = unit_group(owner=1, unit_type="Zealot", count=3, spawn=point_id(1532430764));
    zone_f = circle(center=point_id(1532430748), radius=5);
    zone_g = circle(center=point_id(1532430764), radius=5);
  }
}"""


def test_t02_transition_named_x_func_does_not_collide_with_transition_xs_derived_function_name():
    """A transition literally named `hit_Func` produces trigger variable
    `gt_hit_Func` -- the SAME identifier a transition named `hit` derives
    for its own callback FUNCTION name. Galaxy's global namespace does not
    separate variables from functions, so this is a real collision unless
    both kinds of names share one registry."""
    _assert_no_dup_names_and_compiles(NAME_FUNCTION_CROSS_KIND, transition_id="hit")


NAME_COUNTER_TUPLE = """strategy name_counter_tuple_test {
  world {
    force a_b { side = "enemy"; role = "test"; }
    force a { side = "enemy"; role = "test2"; }
    asset watcher { side = "ally"; role = "test"; }
    region c { role = "test"; }
    region b_c { role = "test2"; }
  }
  initial { alive(a_b); alive(a); alive(watcher); }
  intent { pattern Test; primary alive(watcher); success alive(watcher); failure not (alive(watcher)); }
  plan {
    start [wait1, wait2];
    phase wait1 { purpose "w1"; actors [a_b]; focus [watcher]; }
    phase wait2 { purpose "w2"; actors [a]; focus [watcher]; }
    phase done1 { purpose "d1"; actors [a_b]; focus [watcher]; terminal success; }
    phase done2 { purpose "d2"; actors [a]; focus [watcher]; terminal success; }
    transition t1: wait1 -> done1 { on unit_died(a_b); when (killed_in(a_b, c) >= 1); priority 10; }
    transition t2: wait2 -> done2 { on unit_died(a); when (killed_in(a, b_c) >= 1); priority 10; }
  }
  binding sc2 {
    a_b = unit_group(owner=2, unit_type="Zealot", count=1, spawn=point_id(1532430748));
    a = unit_group(owner=2, unit_type="Zealot", count=1, spawn=point_id(1532430764));
    watcher = unit(owner=1, unit_type="Nexus", at=point_id(1963276538));
    c = circle(center=point_id(1963276538), radius=8);
    b_c = circle(center=point_id(1963276538), radius=9);
  }
}"""


def test_t02_counter_names_for_ambiguous_underscore_concatenation_stay_distinct():
    """killed_in(a_b, c) and killed_in(a, b_c) both naively concatenate to
    "a_b_c" -- two logically different (force, region) counters that must
    not collapse into one shared Galaxy global / monitor trigger."""
    _assert_no_dup_names_and_compiles(NAME_COUNTER_TUPLE)
