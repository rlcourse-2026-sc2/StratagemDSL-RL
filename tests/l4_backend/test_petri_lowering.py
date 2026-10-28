"""Layer 4: v0.6 Petri constructs run correctly as a generated token game."""
from net_harness import Harness

from stratagemdsl.frontend import parse_file
from stratagemdsl.paths import REPO_ROOT


def load(rel):
    return Harness(parse_file(REPO_ROOT / rel, "lark"))


def test_feint_loop_spends_its_budget_then_the_inhibitor_opens_the_strike():
    h = load("examples/learning/05_petri_feint_budget.strat")
    assert h.marked == {"feint", "wait_strike", "fail_watch", "budget"}
    for round_ in range(2):
        h.event("threat")
        assert "regroup" in h.marked and h.tokens("pulled") == round_ + 1
        assert h.tick(go=True) >= {"wait_strike"}          # !budget still blocks the strike
        h.event("again")
        assert h.tokens("budget") == 1 - round_
    h.event("threat")
    assert h.tokens("pulled") == 3
    assert h.event("again") >= {"regroup"}                  # no budget left: the loop stops
    assert "strike" in h.tick(go=True)                      # ?pulled reads, !budget is now empty
    assert h.tokens("pulled") == 3                          # the read arc consumed nothing
    assert h.vm.calls.get("UnitGroupIssueOrder", 0) >= 3    # enemy retargets were issued


def test_fork_and_join_without_a_join_node():
    h = load("examples/petri/swct_fork_trap.strat")
    assert h.event("inserted") >= {"lure", "ramp_guard"}    # one firing, two tokens
    assert "assault_home" not in h.tick(spring=True)        # ?sealed not yet marked
    h.event("seal")
    assert h.tokens("sealed") == 1
    assert "assault_home" in h.tick(spring=True)


def test_inhibitor_arc_blocks_the_trap_after_an_escape():
    h = load("examples/petri/swct_fork_trap.strat")
    h.event("inserted")
    h.event("escape")
    assert h.tokens("aborted") == 1
    h.event("seal")
    assert h.tick(spring=True, give_up=False) >= {"lure"}   # !aborted blocks spring
    assert "withdrawn" in h.tick(give_up=True)
    assert h.outcome == 2


def test_weighted_counter_with_complement_place():
    h = load("examples/learning/04_petri_sync_counter.strat")
    for _ in range(3):
        h.event("count_kill")
    assert h.tokens("kills") == 2 and h.tokens("kill_slots") == 0   # the third death is not counted
    h.event("arrival")
    assert "exploit" in h.tick(release=True)
    assert h.tokens("kills") == 0


def test_round_reset_restores_the_initial_marking():
    h = load("examples/learning/05_petri_feint_budget.strat")
    h.event("threat")
    h.event("again")
    assert h.reset() == {"feint", "wait_strike", "fail_watch", "budget"}
    assert h.tokens("budget") == 2 and h.tokens("pulled") == 0
