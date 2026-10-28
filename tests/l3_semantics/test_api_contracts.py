"""Contract consistency and the actual strict guard -> Galaxy compiler path."""


from stratagemdsl.paths import REPO_ROOT
from stratagemdsl.frontend.antlr_parser import parse_source
from stratagemdsl.semantics.validator import Validator


ROOT = REPO_ROOT

PACKAGE = ROOT

DEMO = ROOT / "tests/fixtures/demos/jctq_api_contract_demo.strat"


def test_aliases_explain_their_real_meaning():
    text = DEMO.read_text().replace("center_passable(exit_zone)", "path_passable(exit_zone)")
    text = text.replace("count_in(escape_force, review_safe_exit)", "apparent_count(escape_force)", 1)
    bag = Validator(parse_source(text)).validate()
    assert not bag.has_errors, [str(x) for x in bag.items]
    warnings = [x.message for x in bag.items if x.code == "W110_LEGACY_API"]
    assert any("center point" in msg for msg in warnings)
    assert any("not observer-visible" in msg for msg in warnings)


def test_side_owner_mismatch_and_unsupported_enemy_order_have_actionable_errors():
    base = DEMO.read_text()
    wrong_owner = base.replace('escape_force = unit_group(owner=1,', 'escape_force = unit_group(owner=2,', 1)
    bag = Validator(parse_source(wrong_owner), strict_sc2=True).validate()
    assert any(d.code == "E014_OWNER_SIDE_MISMATCH" and 'escape_force' in d.message for d in bag.items)
    impossible_order = base.replace('block(enemy_sentries, exit_zone);',
                                    'transport(enemy_sentries, enemy_stalkers, exit_zone);', 1)
    bag = Validator(parse_source(impossible_order), strict_sc2=True).validate()
    assert any(d.code == "E010_BACKEND_CAPABILITY" and 'transport' in d.message for d in bag.items)
