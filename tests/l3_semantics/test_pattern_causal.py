
from stratagemdsl.paths import REPO_ROOT
from stratagemdsl.frontend.lark_parser import parse_source, parse_file
from stratagemdsl.semantics.validator import Validator


ROOT = REPO_ROOT


def validate_text(text: str):
    s = parse_source(text)
    v = Validator(s)
    bag = v.validate()
    return s, v, bag


def test_bound_feint_has_causal_witnesses():
    s = parse_file(ROOT / "tests/fixtures/seeds/sdjx.strat")
    v = Validator(s)
    bag = v.validate()
    assert not bag.has_errors, [str(d) for d in bag.items]
    assert v.pattern_report.passed
    assert {w.code for w in v.pattern_report.witnesses} == {
        "C101_FEINT_THREAT_TO_RELOCATION",
        "C102_FEINT_RELOCATION_TO_WEAKENING",
        "C103_FEINT_WEAKENING_TO_EXPLOIT",
    }


def test_feint_wrong_relocation_target_fails_causal_proof_but_has_same_action_names():
    text = (ROOT / "tests/fixtures/seeds/sdjx.strat").read_text()
    text = text.replace("retarget(defenders, enemy_main);", "retarget(defenders, enemy_expansion);")
    _, v, bag = validate_text(text)
    codes = {d.code for d in bag.items}
    assert "C101_FEINT_THREAT_TO_RELOCATION" in codes
    assert "C102_FEINT_RELOCATION_TO_WEAKENING" in codes
    # Legacy bag-of-actions logic sees retarget+attack and would not catch this.
    assert "C001_FEINT_NO_REDEPLOY" not in codes
    assert "C002_FEINT_NO_EXPLOIT" not in codes


def test_feint_wrong_exploit_target_fails_path_obligation():
    text = (ROOT / "tests/fixtures/seeds/sdjx.strat").read_text()
    text = text.replace("attack(main_force, enemy_expansion);", "attack(main_force, enemy_main);")
    _, _, bag = validate_text(text)
    assert "C103_FEINT_WEAKENING_TO_EXPLOIT" in {d.code for d in bag.items}


def test_pattern_role_type_and_distinctness():
    text = (ROOT / "tests/fixtures/seeds/sdjx.strat").read_text()
    text = text.replace("decoy = feint_force;", "decoy = enemy_main;")
    _, _, bag = validate_text(text)
    assert "C093_PATTERN_ROLE_TYPE" in {d.code for d in bag.items}

    text = (ROOT / "tests/fixtures/seeds/sdjx.strat").read_text()
    text = text.replace("real_target = enemy_expansion;", "real_target = enemy_main;")
    _, _, bag = validate_text(text)
    assert "C095_PATTERN_DISTINCT" in {d.code for d in bag.items}


def test_cerulean_lure_variant_proves_every_lure_obligation():
    s = parse_file(ROOT / "examples/demos/cerulean_lure_zerg_vs_protoss.strat")
    v = Validator(s, strict_sc2=True)
    assert not v.validate().has_errors
    report = v.pattern_report
    assert report.pattern == "Lure" and report.passed
    assert {w.code for w in report.witnesses} == {
        "C111_LURE_STIMULUS_TO_RELOCATION", "C112_LURE_RELOCATION_TO_EXPOSURE", "C113_LURE_EXPOSURE_TO_EXPLOIT"}
