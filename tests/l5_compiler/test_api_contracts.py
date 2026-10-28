"""Contract consistency and the actual strict guard -> Galaxy compiler path."""


from stratagemdsl.paths import REPO_ROOT, compiler_root
from stratagemdsl.frontend.antlr_parser import parse_file
from stratagemdsl.compiler.galaxycc_adapter import compile_galaxy_source
from stratagemdsl.backend.galaxy import lower_to_galaxy
from stratagemdsl.semantics.validator import Validator


ROOT = REPO_ROOT

PACKAGE = ROOT

DEMO = ROOT / "tests/fixtures/demos/jctq_api_contract_demo.strat"


def test_new_path_connected_compiles_through_existing_smac_ast(tmp_path):
    strategy = parse_file(DEMO)
    bag = Validator(strategy, strict_sc2=True).validate()
    assert not bag.has_errors, [str(d) for d in bag.items]
    source, _ = lower_to_galaxy(strategy)
    assert "PointPathingPassable(Point(" in source
    assert "PointPathingIsConnected(Point(" in source
    result = compile_galaxy_source(source, compiler_root(), tmp_path / "demo.galaxy")
    assert result.judge_ok, str(result.judge_result)
    assert result.trigger_xml and result.placed_objects_xml
