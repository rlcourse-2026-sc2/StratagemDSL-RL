"""Layer 6: StormLib / MPQEditor.exe backend selection, and MPQEditor parity.

The parity tests run only where MPQEditor.exe can run (Windows, or wine
elsewhere) and MPQEDITOR_PATH points at it.
"""
import os
import shutil

import pytest

from stratagemdsl import paths
from stratagemdsl.packaging import mpq

TRIGGERS = '<?xml version="1.0" encoding="utf-8"?>\n<TriggerData></TriggerData>\n'
NO_OBJECTS = '<?xml version="1.0" encoding="utf-8"?>\n<PlacedObjects Version="27"></PlacedObjects>\n'

needs_mpqeditor = pytest.mark.skipif(
    not os.environ.get("MPQEDITOR_PATH") or (os.name != "nt" and not shutil.which("wine")),
    reason="set MPQEDITOR_PATH (and install wine outside Windows) to test the MPQEditor backend")


class _Stub:
    backend = "stub"

    def __init__(self, exe, path, readonly=True):
        self.exe, self.path, self.readonly = exe, path, readonly


def test_stormlib_path_follows_the_platform(monkeypatch):
    monkeypatch.delenv("STORMLIB_PATH", raising=False)
    monkeypatch.setattr(paths.sys, "platform", "win32")
    assert paths.stormlib_path().name == "StormLib.dll"
    monkeypatch.setattr(paths.sys, "platform", "linux")
    assert paths.stormlib_path().name == "libstorm.so"


def test_missing_stormlib_falls_back_to_mpqeditor(monkeypatch, tmp_path):
    exe = tmp_path / "MPQEditor.exe"
    exe.write_bytes(b"MZ")
    monkeypatch.setenv("STORMLIB_PATH", str(tmp_path / "missing.so"))
    monkeypatch.delenv("STRAT_MPQ_BACKEND", raising=False)
    monkeypatch.setattr(mpq, "MpqEditorArchive", _Stub)
    monkeypatch.setattr(paths, "mpqeditor_path", lambda: exe)
    archive = mpq.open_archive("map.SC2Map")
    assert isinstance(archive, _Stub) and archive.exe == exe

    monkeypatch.setattr(paths, "mpqeditor_path", lambda: None)
    with pytest.raises(mpq.StormLibUnavailable):
        mpq.open_archive("map.SC2Map")


def test_backend_can_be_forced(monkeypatch, tmp_path):
    exe = tmp_path / "MPQEditor.exe"
    exe.write_bytes(b"MZ")
    monkeypatch.setattr(mpq, "MpqEditorArchive", _Stub)
    monkeypatch.setattr(paths, "mpqeditor_path", lambda: exe)
    monkeypatch.setenv("STRAT_MPQ_BACKEND", "mpqeditor")
    assert isinstance(mpq.open_archive("map.SC2Map"), _Stub)
    monkeypatch.delenv("STRAT_MPQ_BACKEND")
    assert isinstance(mpq.open_archive("map.SC2Map", library=exe), _Stub)


@needs_mpqeditor
def test_mpqeditor_reads_the_same_bytes_as_stormlib():
    base = paths.base_maps_dir() / "cerulean_fall_le.SC2Map"
    with mpq.MpqEditorArchive(os.environ["MPQEDITOR_PATH"], base) as editor, \
            mpq.Archive(paths.stormlib_path(), base) as storm:
        names = storm.names()
        assert editor.names() == names
        for name in names:
            assert editor.read(name) == storm.read(name), name


@needs_mpqeditor
def test_mpqeditor_pack_round_trip(monkeypatch, tmp_path):
    monkeypatch.setenv("STRAT_MPQ_BACKEND", "mpqeditor")
    base = paths.base_maps_dir() / "jctq_te.SC2Map"
    out = tmp_path / "地图" / "out.SC2Map"
    result = mpq.pack_and_verify(base, out, "// probe\n", TRIGGERS, NO_OBJECTS)
    assert result["status"] == "passed" and result["backend"] == "mpqeditor"
    monkeypatch.delenv("STRAT_MPQ_BACKEND")
    with mpq.Archive(paths.stormlib_path(), out) as storm:
        assert storm.read("MapScript.galaxy") == b"// probe\n"
