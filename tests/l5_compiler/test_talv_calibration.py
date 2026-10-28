"""Semantic differences visible in generated code and the historical compiler."""


from stratagemdsl.paths import REPO_ROOT, compiler_root
from stratagemdsl.frontend.antlr_parser import parse_file, parse_source
from stratagemdsl.compiler.galaxycc_adapter import compile_galaxy_source
from stratagemdsl.backend.galaxy import lower_to_galaxy
from stratagemdsl.semantics.validator import Validator


ROOT = REPO_ROOT

PACK = ROOT

DEMO = ROOT / "tests/fixtures/demos/jctq_talv_queue_timeout.strat"


def test_attacker_killer_filters_and_per_unit_idle_event_compile(tmp_path):
    s = parse_file(DEMO)
    galaxy, _ = lower_to_galaxy(s)
    assert 'UnitGroupHasUnit(gv_enemy_sentries, EventUnitTarget()) == true' in galaxy
    assert 'UnitGroupHasUnit(gv_enemy_sentries, libNtve_gf_KillingUnit()) == true' in galaxy
    variant = DEMO.read_text().replace('on enter(escape_force, exit_zone);',
                                       'on unit_became_idle(enemy_sentries);', 1)
    idle = parse_source(variant)
    assert not Validator(idle, strict_sc2=True).validate().has_errors
    idle_galaxy, _ = lower_to_galaxy(idle)
    assert 'TriggerAddEventUnitBecomesIdle(' in idle_galaxy
    assert 'UnitGroupHasUnit(gv_enemy_sentries, EventUnit()) == true' in idle_galaxy
    for name, code in [('attributed', galaxy), ('idle', idle_galaxy)]:
        result = compile_galaxy_source(code, compiler_root(), tmp_path / f'{name}.galaxy')
        assert result.judge_ok, str(result.judge_result)
        assert result.trigger_xml and result.placed_objects_xml


def test_construction_complete_checks_a_live_singleton(tmp_path):
    src = (PACK / 'tests/fixtures/corpus/fkwz_11_ready_pair.strat').read_text()
    src = src.replace('when (alive(enemy_gateway) and',
                      'when (construction_complete(enemy_gateway) and', 1)
    s = parse_source(src)
    bag = Validator(s, strict_sc2=True).validate()
    assert not bag.has_errors, [str(d) for d in bag.items]
    g, _ = lower_to_galaxy(s)
    assert 'UnitGroupCount(gv_enemy_gateway, c_unitCountAlive) > 0' in g
    assert 'libNtve_gf_UnitIsUnderConstruction(UnitGroupUnit(gv_enemy_gateway, 1))' in g
    result = compile_galaxy_source(g, compiler_root(), tmp_path / 'construction.galaxy')
    assert result.judge_ok, str(result.judge_result)
