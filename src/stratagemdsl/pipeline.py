"""The compilation pipeline, one function per layer.

    parse    .strat -> Strategy AST                 (frontend)
    check    AST -> Petri net -> diagnostics        (net + semantics; strict adds the backend probe)
    lower    net -> MapScript.galaxy token game     (backend)
    compile  Galaxy -> galaxycc + plaxtony checks   (compiler; Triggers.xml / Objects.xml)
    pack     Galaxy + XML -> .SC2Map                (packaging)

``run(path, until=...)`` executes the stages in order, stops at ``until`` or at
the first failing stage, and records what happened in a ``Run``.
``write_artifacts`` dumps every intermediate product for inspection.
"""
from __future__ import annotations

import json
import traceback
import xml.etree.ElementTree as ET
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Optional

from stratagemdsl import paths

STAGES = ("parse", "check", "lower", "compile", "pack")


class StageError(RuntimeError):
    def __init__(self, stage: str, message: str):
        super().__init__(f"[{stage}] {message}")
        self.stage = stage


# ---------------------------------------------------------------- stage functions
def parse(path: str | Path, *, frontend: str = "lark", check_agreement: bool = True):
    """Parse with one frontend; optionally require the other to build the same AST."""
    from stratagemdsl.frontend import parse_file
    strategy = parse_file(path, frontend)
    if check_agreement:
        other = "antlr" if frontend == "lark" else "lark"
        if strategy.to_dict() != parse_file(path, other).to_dict():
            raise StageError("parse", f"{frontend} and {other} frontends built different ASTs")
    return strategy


def validate(strategy, *, strict: bool = True, oracle: bool = False):
    """Run the semantic checks and return the Validator (``.diagnostics``, ``.pattern_report``).

    ``strict`` enables the SC2 executability rules, including a dry run of the
    backend as a capability gate (E010_BACKEND_CAPABILITY).
    ``oracle`` makes that dry run emit allied orders, matching ``lower``.
    """
    from stratagemdsl.semantics import Validator
    probe = None
    if strict:
        from stratagemdsl.backend.galaxy import capability_probe

        def probe(candidate, _oracle=oracle):
            return capability_probe(candidate, oracle=_oracle)
    validator = Validator(strategy, strict_sc2=strict, backend_probe=probe)
    validator.validate()
    return validator


def lower(strategy, *, oracle: bool = False, gameover: bool = False):
    """Return the GalaxyLowerer after ``emit()``; the text is ``lowerer.galaxy``.

    ``oracle`` writes allied order actions into the Galaxy program; ``gameover``
    ends the game with GameOver when a terminal phase is reached (one game =
    one scored episode, for LLM agents through PySC2; leave it off for MARL).
    """
    from stratagemdsl.backend.galaxy import GalaxyLowerer
    lowerer = GalaxyLowerer(strategy, oracle=oracle, gameover=gameover)
    lowerer.galaxy = lowerer.emit()
    errors = [k for k, info in lowerer.transition_kinds.items() if info.get("kind") == "error"]
    if errors:
        raise StageError("lower", f"transitions failed to lower: {errors}")
    return lowerer


def compile_galaxy(galaxy: str, *, compiler_root: Optional[Path] = None, source_path: Optional[Path] = None):
    from stratagemdsl.compiler import compile_galaxy_source
    result = compile_galaxy_source(galaxy, compiler_root, source_path)
    if not result.judge_ok:
        raise StageError("compile", str(result.judge_result))
    if not result.trigger_xml or not result.placed_objects_xml:
        raise StageError("compile", "compiler returned empty XML")
    ET.fromstring(result.trigger_xml)
    ET.fromstring(result.placed_objects_xml)
    return result


def pack(galaxy: str, compiled, out_map: Path, *, base_map: Path, stormlib: Optional[Path] = None) -> dict:
    from stratagemdsl.packaging import pack_and_verify
    return pack_and_verify(base_map, out_map, galaxy, compiled.trigger_xml, compiled.placed_objects_xml, stormlib)


# ---------------------------------------------------------------- whole run
@dataclass
class Run:
    source: Path
    until: str
    stages: dict[str, str] = field(default_factory=dict)
    strategy: Any = None
    validator: Any = None
    lowerer: Any = None
    compiled: Any = None
    map_result: Optional[dict] = None
    base_map: Optional[Path] = None   # set by pack; write_artifacts then also writes the routes
    routes: Optional[dict] = None
    failed_stage: Optional[str] = None
    error: Optional[str] = None
    traceback: Optional[str] = None

    @property
    def ok(self) -> bool:
        return self.failed_stage is None

    @property
    def diagnostics(self) -> list[str]:
        return [str(d) for d in self.validator.diagnostics.items] if self.validator else []

    @property
    def galaxy(self) -> Optional[str]:
        return getattr(self.lowerer, "galaxy", None)

    def summary(self) -> dict:
        out = {"source": str(self.source), "until": self.until, "ok": self.ok, "stages": self.stages,
               "diagnostics": self.diagnostics}
        if self.lowerer is not None:
            out["notes"] = sorted(set(self.lowerer.notes))
        if self.validator is not None and getattr(self.validator, "net_report", None) is not None:
            rep = self.validator.net_report
            out["net"] = {**rep.net.stats(), "states": rep.states, "complete": rep.complete,
                          "dead_transitions": [t.id for t in rep.dead_transitions()]}
        if self.compiled is not None:
            out["galaxy_checker"] = self.compiled.checker
        if self.map_result is not None:
            out["map"] = self.map_result
        if self.routes is not None:
            out["routes"] = self.routes
        if not self.ok:
            out.update(failed_stage=self.failed_stage, error=self.error)
        return out


def run(source: str | Path, *, until: str = "compile", strict: bool = True, frontend: str = "lark",
        base_map: Optional[Path] = None, out_dir: Optional[Path] = None,
        compiler_root: Optional[Path] = None, stormlib: Optional[Path] = None,
        oracle: bool = False, gameover: bool = False) -> Run:
    """Run the pipeline up to and including ``until``; never raises for stage failures."""
    if until not in STAGES:
        raise ValueError(f"until must be one of {STAGES}")
    r = Run(Path(source), until)
    stop = STAGES.index(until)
    stage = "parse"
    try:
        r.strategy = parse(r.source, frontend=frontend)
        r.stages[stage] = "passed"
        for stage in STAGES[1:stop + 1]:
            if stage == "check":
                r.validator = validate(r.strategy, strict=strict, oracle=oracle)
                if r.validator.diagnostics.has_errors:
                    raise StageError("check", "; ".join(r.diagnostics))
            elif stage == "lower":
                r.lowerer = lower(r.strategy, oracle=oracle, gameover=gameover)
            elif stage == "compile":
                r.compiled = compile_galaxy(r.galaxy, compiler_root=compiler_root)
            elif stage == "pack":
                if out_dir is None:
                    raise StageError("pack", "pack needs an output directory")
                if base_map:
                    base = Path(base_map)
                else:  # the map the file is written for: cerulean_* -> cerulean_fall_le, arid_* -> arid_plateau, ...
                    from stratagemdsl.views.routes import guess_base_map
                    base = guess_base_map(r.source, paths.base_maps_dir())
                r.base_map = base
                r.map_result = pack(r.galaxy, r.compiled, Path(out_dir) / f"{r.source.stem}.SC2Map",
                                    base_map=base, stormlib=stormlib)
            r.stages[stage] = "passed"
    except Exception as exc:  # recorded, not raised: callers inspect Run
        r.stages[stage] = "failed"
        r.failed_stage, r.error, r.traceback = stage, str(exc), traceback.format_exc()
    if out_dir is not None:
        write_artifacts(r, Path(out_dir))
    return r


def write_artifacts(r: Run, out: Path, stem: Optional[str] = None) -> Path:
    """Write every product the run reached into ``out`` (one file per layer)."""
    out.mkdir(parents=True, exist_ok=True)
    stem = stem or r.source.stem

    def put(name: str, text: str) -> None:
        (out / name).write_text(text, encoding="utf-8")

    if r.strategy is not None:
        put(f"{stem}.ast.json", json.dumps(r.strategy.to_dict(), ensure_ascii=False, indent=2))
    if r.validator is not None:
        put("diagnostics.txt", "\n".join(r.diagnostics) + "\n")
        report = getattr(r.validator, "pattern_report", None)
        if report is not None:
            from stratagemdsl.semantics.patterns.report import format_pattern_report
            put("pattern_report.txt", format_pattern_report(report))
    if r.validator is not None and not r.validator.diagnostics.has_errors:
        from stratagemdsl.backend.intents import agent_intents_json
        put(f"{stem}.agent_intents.json", agent_intents_json(r.strategy))
    if r.validator is not None and getattr(r.validator, "net_report", None) is not None:
        put(f"{stem}.net.json", json.dumps(r.validator.net_report.summary(), ensure_ascii=False, indent=2, default=str))
    if r.lowerer is not None:
        from stratagemdsl.views.plangraph import write_views
        put(f"{stem}.galaxy", r.galaxy)
        put("transition_lowering.json", json.dumps(r.lowerer.transition_kinds, ensure_ascii=False, indent=2))
        write_views(r.strategy, out, stem)
    if r.compiled is not None:
        put("galaxy_check.json", json.dumps({"checker": r.compiled.checker, "skipped": r.compiled.skipped,
                                             "diagnostics": r.compiled.diagnostics}, indent=2))
        put(f"{stem}.Triggers.xml", r.compiled.trigger_xml)
        put(f"{stem}.PlacedObjects.xml", r.compiled.placed_objects_xml)
        put(f"{stem}.TriggerText.txt", r.compiled.trigger_text or "")
    if r.base_map is not None and r.validator is not None and not r.validator.diagnostics.has_errors:
        r.routes = _write_routes(r, out, stem)
    put("result.json", json.dumps(r.summary(), ensure_ascii=False, indent=2) + "\n")
    return out


def _write_routes(r: Run, out: Path, stem: str) -> dict:
    """Movement routes over the base map (views.routes); a failure is recorded, never raised."""
    try:
        from stratagemdsl.views.routes import write_routes
        plan, files = write_routes(r.strategy, r.base_map, out, stem)
    except Exception as exc:  # routes are a view: they must not fail a run
        return {"error": f"{type(exc).__name__}: {exc}"}
    counts: dict[str, int] = {}
    for leg in plan.legs:
        counts[leg.status] = counts.get(leg.status, 0) + 1
    return {"legs": len(plan.legs), "status": counts, "warnings": plan.warnings, "files": files}
