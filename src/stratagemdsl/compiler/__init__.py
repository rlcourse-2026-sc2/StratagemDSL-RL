"""Layer 5: check generated Galaxy and produce the map's trigger documents.

Two independent checkers run on every program:

* ``galaxycc`` -- the vendored smac-ast compiler (``vendor/galaxy_compiler``):
  Lark parse, ``judge`` semantic check, conversion to GUI Triggers.xml /
  PlacedObjects.xml.
* ``plaxtony`` -- the open-source Galaxy language-server checker (MIT,
  ``vendor/galaxy_checker``): parse and full type check against the
  TriggerLibs natives.

``STRAT_GALAXY_CHECKER_BACKEND`` = ``both`` (default) | ``galaxycc`` |
``plaxtony``. With ``both`` a checker that is not installed is skipped and
recorded in ``GalaxyCompileResult.skipped``; at least one must run. Without
galaxycc the trigger XML is an empty TriggerData document (the game runs
MapScript.galaxy itself).
"""
from __future__ import annotations

import os
from pathlib import Path
from typing import Optional

from stratagemdsl import paths
from stratagemdsl.compiler.galaxycc_adapter import GalaxyCompileResult
from stratagemdsl.compiler.galaxycc_adapter import compile_galaxy_source as compile_with_galaxycc
from stratagemdsl.compiler import plaxtony_adapter


def galaxycc_available(compiler_root=None) -> bool:
    root = Path(compiler_root) if compiler_root else paths.compiler_root()
    return (root / "galaxy_v5" / "galaxycc").is_dir()


def selected_backends(compiler_root=None) -> list[str]:
    choice = os.environ.get("STRAT_GALAXY_CHECKER_BACKEND", "both").lower()
    if choice in ("plaxtony", "galaxycc"):
        return [choice]
    out = []
    if galaxycc_available(compiler_root):
        out.append("galaxycc")
    if plaxtony_adapter.available() is None:
        out.append("plaxtony")
    return out


def compile_galaxy_source(source: str, compiler_root=None, source_path=None,
                          backends: Optional[list[str]] = None) -> GalaxyCompileResult:
    backends = backends or selected_backends(compiler_root)
    if not backends:
        raise FileNotFoundError("no Galaxy checker available: neither vendor/galaxy_compiler (galaxycc) nor "
                                "vendor/galaxy_checker (plaxtony; run tools/fetch_galaxy_checker.sh)")
    if source_path is not None:
        Path(source_path).parent.mkdir(parents=True, exist_ok=True)
        Path(source_path).write_text(source, encoding="utf-8")
    result: Optional[GalaxyCompileResult] = None
    if "galaxycc" in backends:
        result = compile_with_galaxycc(source, compiler_root)
        if not result.judge_ok:
            return result
    if "plaxtony" in backends:
        checked = plaxtony_adapter.check_source(source)
        diags = [str(d) for d in checked.diagnostics]
        if result is None:
            result = GalaxyCompileResult(
                checked.ok, "OK" if checked.ok else "; ".join(str(d) for d in checked.errors[:20]),
                trigger_xml=plaxtony_adapter.EMPTY_TRIGGERS if checked.ok else None,
                placed_objects_xml=plaxtony_adapter.EMPTY_OBJECTS if checked.ok else None,
                trigger_text="plaxtony: " + ("; ".join(diags) or "no diagnostics"),
                checker="plaxtony")
        else:
            result.checker = "galaxycc+plaxtony"
            if not checked.ok:
                result.judge_ok = False
                result.judge_result = "plaxtony: " + "; ".join(str(d) for d in checked.errors[:20])
        result.diagnostics = diags
    result.skipped = [b for b in ("galaxycc", "plaxtony") if b not in backends]
    return result


__all__ = ["GalaxyCompileResult", "compile_galaxy_source", "galaxycc_available", "selected_backends",
           "plaxtony_adapter"]
