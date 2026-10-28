"""Differential test: generated Galaxy token game vs the reference net simulator.

For one strategy:

1. lower it with ``guard_oracle=True`` (world guards become bool globals),
2. boot the Galaxy program in `galaxy_vm` and the `TokenGame` in Python,
3. replay random dispatches -- an event of some trigger group or a poll tick,
   with random world-guard values, occasionally a round reset -- on both,
4. after every step compare the full marking, the `once` flags and the
   first_wins outcome.

Any difference is a lowering bug (or a simulator bug); the report names the
step, the trigger and the first differing place.

    python -m stratagemdsl.debug.net_diff FILE.strat [--steps 40 --seeds 5]
"""
from __future__ import annotations

import argparse
import json
import random
import sys
from dataclasses import dataclass, field
from pathlib import Path

from stratagemdsl.backend.galaxy import GalaxyLowerer
from stratagemdsl.backend.galaxy.errors import LoweringError
from lark.exceptions import LarkError
from stratagemdsl.debug.galaxy_vm import GalaxyVM
from stratagemdsl.frontend import parse_file
from stratagemdsl.net import EVENT, POLLED, TokenGame


@dataclass
class DiffResult:
    strategy: str
    steps: int = 0
    fired: int = 0
    resets: int = 0
    mismatches: list[dict] = field(default_factory=list)
    triggers: int = 0
    covered: set = field(default_factory=set)

    @property
    def ok(self) -> bool:
        return not self.mismatches


def _galaxy_state(vm: GalaxyVM, lo: GalaxyLowerer) -> tuple[dict, dict, int]:
    marking = {pid: vm.globals[lo.net_name("m", pid)] for pid in lo.net.places}
    seen = {pid: vm.globals[lo.net_name("seen", pid)] for pid, p in lo.net.places.items() if p.once}
    outcome = vm.globals.get(lo.outcome_global, 0) if lo.outcome_global else 0
    return marking, seen, outcome


def _python_state(game: TokenGame, s) -> tuple[dict, dict, int]:
    marking = game.marking_dict(s)
    seen = {p.id: bool((s.seen >> i) & 1) for i, p in enumerate(game.places) if p.once}
    return marking, seen, s.outcome


def _compare(step, label, vm, lo, game, s, out: DiffResult) -> bool:
    gm, gs, go = _galaxy_state(vm, lo)
    pm, ps, po = _python_state(game, s)
    if (gm, gs, go) == (pm, ps, po):
        return True
    diff = {k: (gm.get(k), pm.get(k)) for k in pm if gm.get(k) != pm.get(k)}
    diff.update({f"seen:{k}": (gs.get(k), ps.get(k)) for k in ps if gs.get(k) != ps.get(k)})
    if go != po:
        diff["outcome"] = (go, po)
    out.mismatches.append({"step": step, "dispatch": label, "galaxy_vs_net": diff})
    return False


def run(strategy, *, steps: int = 40, seeds: int = 5, reset_every: int = 15) -> DiffResult:
    lo = GalaxyLowerer(strategy, guard_oracle=True)
    source = lo.emit()
    result = DiffResult(strategy.name)
    game = TokenGame(lo.net)
    # trigger key -> Galaxy trigger name
    triggers: dict[tuple, str] = {}
    for t in lo.net.transitions:
        info = lo.transition_kinds.get(t.id, {})
        if t.dispatch in (EVENT, POLLED) and "trigger" in info:
            triggers[t.trigger] = info["trigger"]
    result.triggers = len(triggers)
    # Coverage first: replay, for every transition, the analysis' shortest
    # dispatch sequence that fires it; then random exploration.
    from stratagemdsl.net import analyze
    report = analyze(lo.net)
    for tid, path in sorted(report.witnesses().items()):
        vm = GalaxyVM(source)
        vm.boot()
        s = game.initial()
        if not _compare(0, "boot", vm, lo, game, s, result):
            return result
        for i, (key, selected) in enumerate(path, start=1):
            if key not in triggers:
                continue
            chosen = set(selected)
            guards = {}
            for x in game.groups[key]:
                if game.guard(s, x.t) is None:
                    guards[x.id] = x.id in chosen
                    vm.globals[lo.net_name("guard", x.id)] = guards[x.id]
            s = game.step(s, key, lambda t: guards.get(t.id, False))
            vm.run_trigger(triggers[key])
            result.steps += 1
            if not _compare(i, f"witness of {tid}: {triggers[key]} {guards}", vm, lo, game, s, result):
                return result
        result.covered.add(tid)
    for seed in range(seeds):
        rng = random.Random(seed)
        vm = GalaxyVM(source)
        vm.boot()
        s = game.initial()
        if not _compare(0, "boot", vm, lo, game, s, result):
            return result
        for step in range(1, steps + 1):
            result.steps += 1
            if reset_every and step % reset_every == 0:
                vm.run_trigger("gt_Reset")
                s = game.initial()
                result.resets += 1
                if not _compare(step, "reset", vm, lo, game, s, result):
                    return result
                continue
            live = [k for k in triggers if any(game.enabled(s, x) for x in game.groups[k])]
            pool = live if live and rng.random() < 0.85 else list(triggers)
            if not pool:
                break
            key = rng.choice(pool)
            guards = {}
            for x in game.groups[key]:
                if game.guard(s, x.t) is None:
                    guards[x.id] = rng.random() < 0.6
                    vm.globals[lo.net_name("guard", x.id)] = guards[x.id]
            before = s
            s = game.step(s, key, lambda t: guards.get(t.id, False))
            vm.run_trigger(triggers[key])
            if s != before:
                result.fired += 1
            if not _compare(step, f"{triggers[key]} {guards}", vm, lo, game, s, result):
                return result
    return result


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("files", nargs="+", type=Path)
    ap.add_argument("--steps", type=int, default=40)
    ap.add_argument("--seeds", type=int, default=5)
    ap.add_argument("--json", action="store_true")
    a = ap.parse_args(argv)
    bad = 0
    rows = []
    skipped = 0
    for f in a.files:
        # Only sources that reach Galaxy can be compared: a parse error or an
        # action without an SC2 lowering (deliberate in some concept lessons)
        # is reported as skipped, not as a mismatch.
        try:
            strategy = parse_file(f, "lark")
            GalaxyLowerer(strategy, guard_oracle=True).emit()
        except (LarkError, LoweringError, ValueError) as e:
            skipped += 1
            rows.append({"file": str(f), "skipped": f"{type(e).__name__}: {e}"})
            if not a.json:
                print(f"skip {f}  {type(e).__name__}: {str(e)[:160]}")
            continue
        r = run(strategy, steps=a.steps, seeds=a.seeds)
        bad += not r.ok
        rows.append({"file": str(f), "ok": r.ok, "steps": r.steps, "state_changes": r.fired,
                     "covered_transitions": len(r.covered),
                     "resets": r.resets, "triggers": r.triggers, "mismatches": r.mismatches[:1]})
        if not a.json:
            print(f"{'ok ' if r.ok else 'BAD'} {f}  steps={r.steps} changes={r.fired} covered={len(r.covered)} triggers={r.triggers}"
                  + ("" if r.ok else f"  {r.mismatches[0]}"))
    if a.json:
        print(json.dumps(rows, indent=1))
    else:
        print(f"{len(a.files) - skipped - bad} ok, {bad} mismatching, {skipped} skipped (not lowerable)")
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
