"""Layer 3: diagnostics for every bundled source match the recorded baseline.

tests/golden/diagnostics.json was produced by the v0.5 checker. v0.6 adds the
Petri-net analysis (N0xx codes); those are compared against
tests/golden/net_diagnostics.json, everything else must still match v0.5
exactly. Sources missing from this checkout (the v0.4.1/v0.5 lesson corpora
were not shipped) are skipped.
"""
import json

import pytest

from stratagemdsl.frontend import parse_file
from stratagemdsl.paths import REPO_ROOT
from stratagemdsl.semantics import Validator

GOLDEN = json.loads((REPO_ROOT / "tests/golden/diagnostics.json").read_text(encoding="utf-8"))


NET_PATH = REPO_ROOT / "tests/golden/net_diagnostics.json"
NET_GOLDEN = json.loads(NET_PATH.read_text(encoding="utf-8")) if NET_PATH.exists() else {}


@pytest.mark.parametrize("rel", sorted(GOLDEN))
def test_diagnostics_match_baseline(rel):
    if not (REPO_ROOT / rel).exists():
        pytest.skip("source not shipped in this checkout")
    strategy = parse_file(REPO_ROOT / rel, "lark")
    for profile, strict in (("loose", False), ("strict", True)):
        items = Validator(strategy, strict_sc2=strict).validate().items
        classic = [str(d) for d in items if not d.code.startswith("N0")]
        net = [str(d) for d in items if d.code.startswith("N0")]
        assert classic == GOLDEN[rel][profile], profile
        assert net == NET_GOLDEN.get(rel, {}).get(profile, []), profile
