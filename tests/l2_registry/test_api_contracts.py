"""Contract consistency and the actual strict guard -> Galaxy compiler path."""

import pytest
from pydantic import ValidationError

from stratagemdsl.paths import REPO_ROOT
from stratagemdsl.registry.contracts import REGISTRY, contracts, catalog_json, catalog_markdown
from stratagemdsl.registry.builtins import ACTIONS, EVENTS, FUNCTIONS
from stratagemdsl.registry.schema import CallExprS, strategy_json_schema


ROOT = REPO_ROOT

PACKAGE = ROOT

DEMO = ROOT / "tests/fixtures/demos/jctq_api_contract_demo.strat"


def test_type_checker_schema_and_docs_all_come_from_same_registry():
    for ns, table in (("function", FUNCTIONS), ("event", EVENTS), ("action", ACTIONS)):
        assert set(table) == {spec.name for spec in contracts(ns)}
        for name, sigs in table.items():
            assert tuple(sigs) == REGISTRY[(ns, name)].signatures
    enum = strategy_json_schema()["$defs"]["CallExprS"]["properties"]["name"]["enum"]
    assert set(enum) == {name for _, name in REGISTRY}
    assert len(catalog_json()["apis"]) == len(REGISTRY)
    assert "PointPathingIsConnected" in catalog_markdown()
    with pytest.raises(ValidationError, match="unknown StratagemDSL API"):
        CallExprS(name="imaginary_count", args=[])
