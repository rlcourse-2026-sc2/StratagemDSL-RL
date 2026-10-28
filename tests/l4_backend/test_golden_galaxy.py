"""Layer 4: generated Galaxy for every bundled source is byte-identical to the baseline.

tests/golden/galaxy_sha256.json was produced by the pre-restructure code.
Inspect a difference with: python -m stratagemdsl.backend FILE
"""
import hashlib
import json

import pytest

from stratagemdsl.backend.galaxy import GalaxyLowerer
from stratagemdsl.frontend import parse_file
from stratagemdsl.paths import REPO_ROOT

GOLDEN = json.loads((REPO_ROOT / "tests/golden/galaxy_sha256.json").read_text(encoding="utf-8"))


@pytest.mark.parametrize("rel", sorted(GOLDEN))
def test_galaxy_matches_baseline(rel):
    try:
        galaxy = GalaxyLowerer(parse_file(REPO_ROOT / rel, "lark")).emit()
        got = hashlib.sha256(galaxy.encode("utf-8")).hexdigest()
    except Exception as exc:
        got = f"lowering_error: {type(exc).__name__}: {exc}"
    assert got == GOLDEN[rel]


def test_every_registered_extension_has_a_lowering():
    from stratagemdsl.backend.galaxy import extensions as ext
    from stratagemdsl.registry import extensions as api
    assert set(api.FUNCS) == set(ext.LOWER_FN)
    assert set(api.EVS) == set(ext.LOWER_EV)
    assert set(api.ACTS) == set(ext.LOWER_ACT)
