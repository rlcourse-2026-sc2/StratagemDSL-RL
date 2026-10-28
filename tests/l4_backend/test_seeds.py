
from stratagemdsl.paths import REPO_ROOT
from stratagemdsl.frontend.lark_parser import parse_file
from stratagemdsl.semantics.validator import Validator
from stratagemdsl.backend.galaxy import lower_to_galaxy


ROOT = REPO_ROOT

NAMES = ["adcc","dhls","fkwz","gmzz","jctq","jdsr","sdjx","swct","tlhz","wwjz","wzsy","yqgz"]


def test_all12_parse_validate_lower():
    for name in NAMES:
        s = parse_file(ROOT / "tests/fixtures/seeds" / f"{name}.strat")
        bag = Validator(s).validate()
        assert not bag.has_errors, (name, [str(x) for x in bag.items])
        galaxy, notes = lower_to_galaxy(s)
        assert 'void InitMap ()' in galaxy
        assert 'void gf_Spawn ()' in galaxy
