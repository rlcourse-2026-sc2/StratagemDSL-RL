"""Semantic differences visible in generated code and the historical compiler."""


from stratagemdsl.paths import REPO_ROOT
from stratagemdsl.frontend.antlr_parser import parse_file, parse_source
from stratagemdsl.frontend.lark_parser import parse_file as parse_bootstrap
from stratagemdsl.backend.galaxy import GalaxyLowerer, lower_to_galaxy
from stratagemdsl.semantics.validator import Validator


ROOT = REPO_ROOT

PACK = ROOT

DEMO = ROOT / "tests/fixtures/demos/jctq_talv_queue_timeout.strat"


def test_sequence_queues_per_actor_and_parallel_replaces():
    base = DEMO.read_text()
    s = parse_source(base)
    bag = Validator(s, strict_sc2=True).validate()
    assert not bag.has_errors, [str(d) for d in bag.items]
    galaxy, _ = lower_to_galaxy(s)
    assert 'c_orderQueueAddToEnd' in galaxy
    assert "W102_REPLACED_ORDER" not in {d.code for d in bag.items}

    # Compare the same two immediately issued orders in each block mode.
    base = base.replace('do { block(enemy_sentries, exit_zone);', 'do sequence { block(enemy_sentries, exit_zone);', 1)
    ordered = base.replace('block(enemy_sentries, exit_zone);', 'move(enemy_sentries, exit_zone);', 1)
    parallel = ordered.replace('do sequence { move(enemy_sentries, exit_zone);',
                               'do parallel { move(enemy_sentries, exit_zone);', 1)
    p = parse_source(parallel)
    pbag = Validator(p, strict_sc2=True).validate()
    assert not pbag.has_errors, [str(d) for d in pbag.items]
    assert any(d.code == 'W102_REPLACED_ORDER' for d in pbag.items)
    phase = next(n for n in p.plan.nodes if n.id == 'exit_blocked')
    lines = GalaxyLowerer(p)._emit_action_block(phase.actions)
    assert len([line for line in lines if 'c_orderQueueReplace' in line]) == 2
    assert not any('c_orderQueueAddToEnd' in line for line in lines)
    # Ability orders are also replaced in parallel; the warning must cover
    # them rather than just move/attack/hold.
    ability_parallel = base.replace('do sequence { block(enemy_sentries, exit_zone);',
                                    'do parallel { block(enemy_sentries, exit_zone);', 1)
    assert any(d.code == 'W102_REPLACED_ORDER'
               for d in Validator(parse_source(ability_parallel), strict_sc2=True).validate().items)
    allied_parallel = base.replace('do { cast(escape_force, "Burrow"); }',
                                   'do parallel { move(escape_force, exit_zone); cast(escape_force, "Burrow"); }', 1)
    assert 'W102_REPLACED_ORDER' not in {
        d.code for d in Validator(parse_source(allied_parallel), strict_sc2=True).validate().items
    }


def test_numeric_derive_and_absolute_timeout_are_typed_and_polled():
    s = parse_file(DEMO)
    assert s.to_dict() == parse_bootstrap(DEMO).to_dict()
    v = Validator(s, strict_sc2=True)
    assert not v.validate().has_errors
    assert v.symbol_types['escaped_units'] == 'Int'
    assert v.symbol_types['deadline'] == 'Bool'
    g, _ = lower_to_galaxy(s)
    assert 'GameGetMissionTime()' in g
    assert 'TriggerAddEventTimePeriodic(gt_net_tick, 1.0, c_timeGame)' in g
    assert 'GameGetMissionTime() >= 30' in g
    negative = DEMO.read_text().replace('after(30)', 'after(-1)', 1)
    bag = Validator(parse_source(negative)).validate()
    assert 'T080_NEGATIVE_TIME' in {d.code for d in bag.items}
