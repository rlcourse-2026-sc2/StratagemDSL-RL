"""Layer 6: map packing writes exactly three members and preserves the rest.

Uses hand-written Galaxy/XML so it does not depend on the compiler layer.
"""
import pytest

from stratagemdsl import paths
from stratagemdsl.packaging.mpq import merge_objects, pack_and_verify

needs_stormlib = pytest.mark.skipif(
    not paths.stormlib_path().is_file() and paths.mpqeditor_path() is None,
    reason="no StormLib build for this system; set STORMLIB_PATH or MPQEDITOR_PATH")

TRIGGERS = '<?xml version="1.0" encoding="utf-8"?>\n<TriggerData></TriggerData>\n'
NO_OBJECTS = '<?xml version="1.0" encoding="utf-8"?>\n<PlacedObjects Version="27"></PlacedObjects>\n'


@needs_stormlib
def test_pack_replaces_script_and_triggers_and_keeps_other_members(tmp_path):
    base = paths.base_maps_dir() / "jctq_te.SC2Map"
    before = base.read_bytes()
    result = pack_and_verify(base, tmp_path / "out.SC2Map", "// probe\n", TRIGGERS, NO_OBJECTS)
    assert result["status"] == "passed"
    assert result["replaced_members"] == ["MapScript.galaxy", "Triggers", "Objects"]
    assert result["objects_preserved_exactly"] and result["preserved_members"] > 0
    assert base.read_bytes() == before, "base map must stay untouched"


@needs_stormlib
def test_pack_refuses_to_overwrite_the_base_map():
    base = paths.base_maps_dir() / "jctq_te.SC2Map"
    with pytest.raises(ValueError, match="immutable"):
        pack_and_verify(base, base, "// probe\n", TRIGGERS, NO_OBJECTS)


def test_object_merge_rejects_id_collisions():
    base = '<PlacedObjects><ObjectPoint Id="7"/></PlacedObjects>'
    merged, added = merge_objects(base, '<PlacedObjects><ObjectPoint Id="8"/></PlacedObjects>')
    assert added == 1 and b'Id="8"' in merged
    with pytest.raises(ValueError, match="collision"):
        merge_objects(base, '<PlacedObjects><ObjectPoint Id="7"/></PlacedObjects>')
