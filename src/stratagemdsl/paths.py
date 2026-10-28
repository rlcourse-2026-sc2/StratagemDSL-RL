"""Locations of the repository-level assets the upper layers need.

Each can be overridden with an environment variable so an installed package
can point at an external checkout.
"""
from __future__ import annotations

import os
import shutil
import sys
from pathlib import Path
from typing import Optional

REPO_ROOT = Path(__file__).resolve().parents[2]


def _env_path(name: str, default: Path) -> Path:
    value = os.environ.get(name)
    return Path(value) if value else default


def compiler_root() -> Path:
    """Vendored galaxycc checkout (galaxy_v5/ + database/)."""
    return _env_path("STRAT_COMPILER_ROOT", _env_path("SMAC_AST_ROOT", REPO_ROOT / "vendor" / "galaxy_compiler"))


def galaxy_checker_dir() -> Path:
    """Open-source Galaxy checker (plaxtony driver + TriggerLibs headers)."""
    return _env_path("STRAT_GALAXY_CHECKER", REPO_ROOT / "vendor" / "galaxy_checker")


def base_maps_dir() -> Path:
    return _env_path("STRAT_BASE_MAPS", REPO_ROOT / "assets" / "base_maps")


STORMLIB_NAMES = {"win32": "StormLib.dll", "darwin": "libstorm.dylib"}


def stormlib_path() -> Path:
    """Native StormLib for this OS (bundled: Linux x86-64 and Windows x64)."""
    name = STORMLIB_NAMES.get(sys.platform, "libstorm.so")
    return _env_path("STORMLIB_PATH", REPO_ROOT / "assets" / "native" / name)


def mpqeditor_path() -> Optional[Path]:
    """Ladik's MPQEditor.exe, the alternative map backend (MPQEDITOR_PATH, assets/native/, or PATH)."""
    candidates = [os.environ.get("MPQEDITOR_PATH"), REPO_ROOT / "assets" / "native" / "MPQEditor.exe",
                  shutil.which("MPQEditor.exe"), shutil.which("MPQEditor")]
    for c in candidates:
        if c and Path(c).is_file():
            return Path(c)
    return None


def build_dir() -> Path:
    return _env_path("STRAT_BUILD_DIR", REPO_ROOT / "build")
