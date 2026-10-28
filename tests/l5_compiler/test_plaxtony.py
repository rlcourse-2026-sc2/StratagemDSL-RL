"""Layer 5: the open-source plaxtony checker accepts generated Galaxy and catches errors."""
import pytest

from stratagemdsl.backend.galaxy import GalaxyLowerer
from stratagemdsl.compiler import plaxtony_adapter
from stratagemdsl.frontend import parse_file
from stratagemdsl.paths import REPO_ROOT

pytestmark = pytest.mark.skipif(plaxtony_adapter.available() is not None,
                                reason=str(plaxtony_adapter.available()))

FILES = (sorted((REPO_ROOT / "examples").glob("*/*.strat"))
         + sorted((REPO_ROOT / "tests/fixtures/corpus").glob("*.strat")))
FILES = [f for f in FILES if f.parent.name != "petri_negative"]


def test_generated_programs_type_check_without_any_diagnostic():
    sources = {str(f): GalaxyLowerer(parse_file(f, "lark")).emit() for f in FILES}
    results = plaxtony_adapter.check_sources(sources)
    bad = {k: [str(d) for d in r.diagnostics] for k, r in results.items() if r.diagnostics}
    assert not bad, bad


def test_type_errors_are_reported():
    galaxy = GalaxyLowerer(parse_file(REPO_ROOT / "examples/learning/05_petri_feint_budget.strat", "lark")).emit()
    broken = galaxy.replace("gv_net_m_budget = 2;", "gv_net_m_budget = true;", 1)
    result = plaxtony_adapter.check_source(broken)
    assert not result.ok
    assert any("not assignable" in d.message for d in result.errors)
