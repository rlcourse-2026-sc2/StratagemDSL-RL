"""Follow the plan from what one player observes (fog of war included).

An agent does not see the map script's marking. `PlanTracker` replays the
plan's Petri net on the events an agent can observe -- its own forces
entering/leaving regions and losing units, enemy forces it sees -- with the
world guards evaluated on the observation (`play.worldguards`): own forces
are known exactly, an enemy force only while some of it is visible (else
unknown, so a guard that needs it does not fire). The result is an
estimate of the current phases, used to brief an agent ("which step of
the plan are we in") and by the offline planner in LLM-PySC2.

It never commands anything and it may lag or miss transitions the real
script takes (e.g. on an enemy unit it cannot see dying). With
``optimistic_events=True`` (the default) an event we did observe -- say our
bait entering the lure zone -- fires its transition unless the guard is
known to be false: the map script sees what we cannot (the enemy guard's
distance to its base), and a guard we cannot decide is more often true
than not when the plan's own event happens. Polled transitions still need
a guard that is known to hold.
"""
from __future__ import annotations

import math
from typing import Optional

from stratagemdsl.core.model import Phase, Strategy
from stratagemdsl.net import StepLog, TokenGame, build_net
from stratagemdsl.play.game import LOOPS_PER_SECOND, Frame
from stratagemdsl.play.observe import ForceTracker
from stratagemdsl.play.scenario import Scenario
from stratagemdsl.play.worldguards import truth


class _ObservedWorld:
    def __init__(self, tracker: ForceTracker, loop_ref):
        self.t = tracker
        self.sc = tracker.sc
        self._loop = loop_ref

    def _own(self, name: str) -> bool:
        return self.sc.forces[name].owner == self.t.player_id

    def count(self, name: str) -> Optional[int]:
        st = self.t.states.get(name)
        if st is None:
            return None
        if self._own(name):
            return len(st.alive)
        return len(st.alive) if st.alive else None

    def centroid(self, name: str) -> Optional[tuple[float, float]]:
        st = self.t.states.get(name)
        return st.centroid if st is not None else None

    def count_in(self, name: str, region: str) -> Optional[int]:
        st = self.t.states.get(name)
        loc = self.sc.regions.get(region)
        if st is None or loc is None:
            return None
        n = sum(1 for u in st.alive if math.hypot(u.x - loc.x, u.y - loc.y) <= loc.radius)
        if n == 0 and not self._own(name) and not st.alive:
            return None
        return n

    def targeting(self, a: str, b: str) -> Optional[bool]:
        return None

    def killed_in(self, force: str, region: str) -> Optional[int]:
        return None

    def seconds(self) -> float:
        return self._loop() / LOOPS_PER_SECOND

    def elapsed(self, phase: str) -> Optional[float]:
        return None


class PlanTracker:
    def __init__(self, strategy: Strategy, scenario: Scenario, tracker: Optional[ForceTracker] = None, *,
                 optimistic_events: bool = True):
        self.strategy = strategy
        self.optimistic_events = optimistic_events
        self.sc = scenario
        self.net = build_net(strategy)
        self.game = TokenGame(self.net)
        self.tracker = tracker or ForceTracker(scenario)
        self.phases = {n.id: n for n in strategy.plan.nodes if isinstance(n, Phase)}
        self.keys = [k for k in self.game.groups if k[0] == "event"]
        self.reset()

    def reset(self) -> None:
        self.loop = 0
        self.cursor = 0
        self.entered_at: dict[str, int] = {}
        self.history: list[dict] = []
        self.counts: dict[str, int] = {}
        self.world = _ObservedWorld(self.tracker, lambda: self.loop)
        log = StepLog()
        self.state = self.game.initial(log)
        self._record(log, "start")

    # ------------------------------------------------------------ update
    def update(self, frame: Frame, *, update_tracker: bool = False) -> None:
        if update_tracker:
            self.tracker.update(frame)
        self.loop = frame.game_loop
        occurrences = []
        for e in self.tracker.events[self.cursor:]:
            if e["event"] in ("enter", "leave"):
                occurrences.append((e["event"], (e["force"], e["region"])))
        self.cursor = len(self.tracker.events)
        for name, st in self.tracker.states.items():   # deaths of own units (enemies: only visible ones)
            n = len(st.alive)
            before = self.counts.get(name)
            if before is not None and n < before and (self.sc.forces[name].owner == self.tracker.player_id or n > 0):
                occurrences += [("unit_died", (name,))] * (before - n)
            self.counts[name] = n
        if self.state.outcome:
            return
        oracle = self._oracle_event if self.optimistic_events else self._oracle
        for name, args in occurrences:
            for key in self.keys:
                evname, kargs = key[1]
                named = [v for kind, v in kargs if kind == "name"]
                if evname == name and len(named) <= len(args) and list(args[:len(named)]) == named:
                    log = StepLog()
                    self.state = self.game.step(self.state, key, oracle, log)
                    self._record(log, f"{name}({', '.join(args)})")
        for key in self.keys:
            evname, kargs = key[1]
            if evname == "timer" and len(kargs) >= 2:
                place, secs = kargs[0][1], float(kargs[1][1])
                at = self.entered_at.get(place)
                if at is not None and (self.loop - at) / LOOPS_PER_SECOND >= secs:
                    log = StepLog()
                    self.state = self.game.step(self.state, key, oracle, log)
                    if log.fired:
                        self._record(log, f"timer({place}, {secs:g})")
        if ("poll",) in self.game.groups:
            log = StepLog()
            self.state = self.game.step(self.state, ("poll",), self._oracle, log)
            self._record(log, "poll")

    def _oracle(self, t) -> bool:
        return truth(t.guard, self.game.marking_dict(self.state), self.net.derived, self.world) is True

    def _oracle_event(self, t) -> bool:
        return truth(t.guard, self.game.marking_dict(self.state), self.net.derived, self.world) is not False

    def _record(self, log: StepLog, cause: str) -> None:
        for p in log.left:
            self.entered_at.pop(p, None)
        for p in log.entered:
            self.entered_at[p] = self.loop
        if log.fired or log.entered:
            fired = [self.game.ts[t].t.origin for t in log.fired if self.game.ts[t].t.origin]
            self.history.append({"loop": self.loop, "cause": cause, "fired": fired, "entered": list(log.entered)})

    # ----------------------------------------------------------- queries
    def active_phases(self) -> list[str]:
        marked = self.game.marked(self.state)
        return [p for p in marked if p in self.phases]

    def orders_for(self, force: str) -> list[str]:
        """The plan's orders for `force` in the phases believed active."""
        from stratagemdsl.frontend.unparse import _print_expr
        out = []
        for pid in self.active_phases():
            ph = self.phases[pid]
            for call in (ph.actions.actions if ph.actions else []):
                if call.args and getattr(call.args[0], "name", None) == force:
                    out.append(_print_expr(call))
        return out

    def expected_events(self, force: str) -> list[str]:
        """Events of `force` the plan waits for next (transitions whose input places are marked), e.g.
        enter(allied_force, nydus_lure_zone): what the plan expects the force to do when it gives no order."""
        from stratagemdsl.frontend.unparse import _print_expr
        marked = self.game.marked(self.state)
        out = []
        for t in self.strategy.plan.transitions:
            ins = [a.place for a in t.inputs if a.kind in ("normal", "read")]
            if t.event is None or not ins or not all(p in marked for p in ins):
                continue
            if t.event.args and getattr(t.event.args[0], "name", None) == force:
                text = _print_expr(t.event)
                if text not in out:
                    out.append(text)
        return out

    def describe(self) -> str:
        active = self.active_phases()
        lines = ["Plan progress as you can observe it (estimate; the map script may be ahead):",
                 f"- active phases: {', '.join(active) or 'none'}"]
        for pid in active:
            lines.append(f"  - {pid}: {self.phases[pid].purpose}")
        for h in self.history[-4:]:
            if h["fired"]:
                mm, ss = divmod(int(h["loop"] / LOOPS_PER_SECOND), 60)
                lines.append(f"- {mm:02d}:{ss:02d} {', '.join(h['fired'])} (on {h['cause']}) -> {', '.join(h['entered'])}")
        outcome = {1: "success", 2: "failure"}.get(self.state.outcome)
        if outcome:
            lines.append(f"- the plan has reached {outcome}")
        return "\n".join(lines)
