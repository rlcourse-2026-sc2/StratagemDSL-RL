import pytest

from stratagemdsl.paths import REPO_ROOT
from stratagemdsl.frontend.lark_parser import parse_file, parse_source
from stratagemdsl.semantics.patterns.library import PATTERNS
from stratagemdsl.semantics.patterns.ontology import CONCEPTS, OPERATORS, validate_operator_names
from stratagemdsl.semantics.validator import Validator


ROOT = REPO_ROOT


def validate_example(name: str):
    strategy = parse_file(ROOT / "tests/fixtures/seeds" / name)
    validator = Validator(strategy)
    bag = validator.validate()
    return validator, bag


def test_public_ontology_has_expected_families_and_twelve_operators():
    assert {x.family for x in CONCEPTS.values()} >= {
        "entity", "space", "resource", "epistemic", "state",
        "relation", "opportunity", "utility",
    }
    assert len(OPERATORS) == 12
    assert {"Deceive", "Conceal", "Induce", "Redirect", "Weaken", "Isolate", "Exploit"} <= set(OPERATORS)


def test_every_migrated_pattern_composes_known_operators():
    for pattern in PATTERNS.values():
        assert validate_operator_names(pattern.composed_from) == (), pattern.name


@pytest.mark.parametrize(
    "filename,codes",
    [
        ("sdjx.strat", {"C101_FEINT_THREAT_TO_RELOCATION", "C102_FEINT_RELOCATION_TO_WEAKENING", "C103_FEINT_WEAKENING_TO_EXPLOIT"}),
        ("dhls.strat", {"C111_LURE_STIMULUS_TO_RELOCATION", "C112_LURE_RELOCATION_TO_EXPOSURE", "C113_LURE_EXPOSURE_TO_EXPLOIT"}),
        ("wwjz.strat", {"C121_RELIEF_THREAT_TO_REDIRECT", "C122_RELIEF_REDIRECT_TO_RELIEF", "C123_RELIEF_TO_INTERCEPT"}),
        ("adcc.strat", {"C131_BYPASS_CONCEAL_TO_REAR", "C132_BYPASS_REAR_TO_EXPLOIT"}),
    ],
)
def test_migrated_patterns_produce_complete_causal_witnesses(filename, codes):
    validator, bag = validate_example(filename)
    assert not bag.has_errors, [str(d) for d in bag.items]
    assert validator.pattern_report.passed
    assert {w.code for w in validator.pattern_report.witnesses} == codes


def test_lure_rejects_wrong_enemy_relocation_even_when_move_and_attack_remain():
    text = (ROOT / "tests/fixtures/seeds/dhls.strat").read_text(encoding="utf-8")
    text = text.replace("move(enemy_guard_force, nydus_enemy_target);", "move(enemy_guard_force, pathway_midpoint);", 1)
    strategy = parse_source(text)
    validator = Validator(strategy)
    bag = validator.validate()
    codes = {d.code for d in bag.items}
    assert "C111_LURE_STIMULUS_TO_RELOCATION" in codes
    assert "C112_LURE_RELOCATION_TO_EXPOSURE" in codes


def test_indirect_relief_rejects_retarget_that_does_not_leave_protected_target():
    text = (ROOT / "tests/fixtures/seeds/wwjz.strat").read_text(encoding="utf-8")
    text = text.replace("retarget(enemy_siege_force, relief_force);", "retarget(enemy_siege_force, besieged_base);")
    strategy = parse_source(text)
    validator = Validator(strategy)
    bag = validator.validate()
    assert "C121_RELIEF_THREAT_TO_REDIRECT" in {d.code for d in bag.items}


def test_covert_bypass_requires_actual_concealment_not_just_move_and_attack():
    text = (ROOT / "tests/fixtures/seeds/adcc.strat").read_text(encoding="utf-8")
    text = text.replace('cast(allied_force, "Burrow"); ', "")
    strategy = parse_source(text)
    validator = Validator(strategy)
    bag = validator.validate()
    codes = {d.code for d in bag.items}
    assert "C131_BYPASS_CONCEAL_TO_REAR" in codes
    assert "C132_BYPASS_REAR_TO_EXPLOIT" in codes
