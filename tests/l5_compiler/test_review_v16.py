"""
Regression tests for the v16-review findings (S01-S04): two leftover gaps
in earlier fixes (S01, S03) and two genuine new regressions the earlier
fixes themselves introduced (S02, S04).
"""

import re
from pathlib import Path

from stratagemdsl.paths import compiler_root
from stratagemdsl.frontend.antlr_parser import parse_source
from stratagemdsl.semantics.validator import Validator
from stratagemdsl.backend.galaxy import lower_to_galaxy
from stratagemdsl.compiler.galaxycc_adapter import compile_galaxy_source


COMPILER_ROOT = str(compiler_root())

JOIN_INITIAL_BOTH = """strategy join_initial_both_test {
  world {
    force enemy { side = "enemy"; role = "test"; }
    asset watcher { side = "ally"; role = "test"; }
  }
  initial { alive(enemy); alive(watcher); }
  intent { pattern Test; primary alive(watcher); success alive(watcher); failure not (alive(watcher)); }
  plan {
    start [left, right];
    phase left { purpose "l"; actors [enemy]; focus [watcher]; }
    phase right { purpose "r"; actors [enemy]; focus [watcher]; }
    join ready all;
    phase done { purpose "done"; actors [enemy]; focus [watcher]; do { hold(enemy); } terminal success; }
    transition a: left -> ready { when true; priority 10; }
    transition b: right -> ready { when true; priority 10; }
    transition tail: ready -> done { when true; priority 10; }
  }
  binding sc2 {
    enemy = unit_group(owner=2, unit_type="Zealot", count=2, spawn=point_id(1532430748));
    watcher = unit(owner=1, unit_type="Nexus", at=point_id(1963276538));
  }
}"""

COUNTER_UNARY_NEG = """strategy counter_unary_neg_test {
  world {
    force enemy { side = "enemy"; role = "test"; }
    asset watcher { side = "ally"; role = "test"; }
    region zone { role = "test"; }
  }
  initial { alive(enemy); alive(watcher); }
  intent { pattern Test; primary alive(watcher); success alive(watcher); failure not (alive(watcher)); }
  plan {
    start [wait];
    phase wait { purpose "wait"; actors [enemy]; focus [watcher]; }
    phase done { purpose "done"; actors [enemy]; focus [watcher]; terminal success; }
    transition finish: wait -> done {
      on unit_died(enemy);
      when (killed_in(enemy, zone) + (-(killed_in(enemy, zone))) == 0);
      priority 10;
    }
  }
  binding sc2 {
    enemy = unit_group(owner=2, unit_type="Zealot", count=1, spawn=point_id(1532430748));
    watcher = unit(owner=1, unit_type="Nexus", at=point_id(1963276538));
    zone = circle(center=point_id(1963276538), radius=8);
  }
}"""

EVENT_PRIORITY = """strategy event_priority_test {
  world {
    force enemyA { side = "enemy"; role = "test"; }
    force enemyB { side = "enemy"; role = "test"; }
    force actor { side = "ally"; role = "test"; }
    region zone { role = "test"; }
  }
  initial { alive(enemyA); alive(enemyB); alive(actor); }
  intent { pattern Test; primary alive(actor); success alive(actor); failure not (alive(actor)); }
  plan {
    start [begin];
    phase begin { purpose "b"; actors [actor]; focus [actor]; }
    phase left { purpose "l"; actors [actor]; focus [actor]; terminal success; }
    phase right { purpose "r"; actors [actor]; focus [actor]; terminal failure; }
    transition to_left: begin -> left {
      on enter(enemyA, zone);
      when (count(enemyA) > 0);
      priority 20;
    }
    transition to_right: begin -> right {
      on enter(enemyA, zone);
      when (count(enemyB) > 0);
      priority 10;
    }
  }
  binding sc2 {
    enemyA = unit_group(owner=2, unit_type="Zealot", count=3, spawn=point_id(1532430748));
    enemyB = unit_group(owner=2, unit_type="Zealot", count=3, spawn=point_id(1532430764));
    actor = unit_group(owner=1, unit_type="Zealot", count=1, spawn=point_id(1963276538));
    zone = circle(center=point_id(1963276538), radius=8);
  }
}"""

TRIGGER_NAME_COLLISION = """strategy trigger_name_collision_test {
  world {
    force enemy { side = "enemy"; role = "test"; }
    asset watcher { side = "ally"; role = "test"; }
    region zone { role = "test"; }
  }
  initial { alive(enemy); alive(watcher); }
  intent { pattern Test; primary alive(watcher); success alive(watcher); failure not (alive(watcher)); }
  plan {
    start [wait, other];
    phase wait { purpose "w"; actors [enemy]; focus [watcher]; }
    phase other { purpose "o"; actors [enemy]; focus [watcher]; }
    phase done { purpose "d"; actors [enemy]; focus [watcher]; terminal success; }
    transition wait_done: wait -> done { when (count(enemy) > 0); priority 10; }
    transition poll_wait: other -> done { on leave(enemy, zone); priority 10; }
  }
  binding sc2 {
    enemy = unit_group(owner=2, unit_type="Zealot", count=2, spawn=point_id(1532430748));
    watcher = unit(owner=1, unit_type="Nexus", at=point_id(1963276538));
    zone = circle(center=point_id(1963276538), radius=8);
  }
}"""


def test_s04_auto_generated_dispatcher_name_never_collides_with_a_user_transition_id():
    """S04: a legally-named user transition `poll_wait` (-> `gt_poll_wait`)
    must not collide with the auto-generated combined poll dispatcher for
    an UNRELATED source `wait` (which also wants `gt_poll_wait`). Both must
    end up with distinct Galaxy trigger names, and the result must actually
    compile through the real smac-ast compiler (a real duplicate produces
    a ScopeError there, not just a Python-side symptom)."""
    s = parse_source(TRIGGER_NAME_COLLISION)
    bag = Validator(s).validate()
    assert not [x for x in bag.items if "ERROR" in str(x).upper()]

    galaxy, _ = lower_to_galaxy(s)
    names = re.findall(r"trigger (gt_\w+);", galaxy)
    assert len(names) == len(set(names)), f"duplicate trigger names: {names}"

    import tempfile
    with tempfile.TemporaryDirectory() as tmpdir:
        result = compile_galaxy_source(
            galaxy, compiler_root=COMPILER_ROOT,
            source_path=str(Path(tmpdir) / "s04_test_output.galaxy"),
        )
    assert result.judge_ok, result.judge_result
