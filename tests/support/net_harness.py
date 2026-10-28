"""Run a strategy's generated Galaxy token game next to the reference net simulator.

Every step is applied to both and the markings must agree, so a test written
against `Harness` checks the plan semantics *and* the lowering at once:

    h = Harness(SOURCE)
    h.event("a")                 # fire the trigger that dispatches transition a
    h.tick(finish=True)          # one poll tick, world guard of `finish` true
    assert h.marked == {"done"}
"""
from __future__ import annotations

from stratagemdsl.backend.galaxy import GalaxyLowerer
from stratagemdsl.debug.galaxy_vm import GalaxyVM
from stratagemdsl.frontend.antlr_parser import parse_source
from stratagemdsl.net import EVENT, POLLED, TokenGame


class Harness:
    def __init__(self, source, *, oracle_guards: bool = True):
        self.strategy = parse_source(source) if isinstance(source, str) else source
        self.lo = GalaxyLowerer(self.strategy, guard_oracle=oracle_guards)
        self.galaxy = self.lo.emit()
        self.vm = GalaxyVM(self.galaxy)
        self.vm.boot()
        self.game = TokenGame(self.lo.net)
        self.state = self.game.initial()
        self.history: list[str] = ["boot"]
        self._check()

    # ------------------------------------------------------------ state
    @property
    def marking(self) -> dict[str, int]:
        return {p: self.vm.globals[self.lo.net_name("m", p)] for p in self.lo.net.places}

    @property
    def marked(self) -> set[str]:
        """Marked DSL-visible places (phases, joins, token places)."""
        return {p for p, n in self.marking.items() if n and self.lo.net.places[p].is_control}

    @property
    def outcome(self) -> int:
        return self.vm.globals.get(self.lo.outcome_global, 0) if self.lo.outcome_global else 0

    def tokens(self, place: str) -> int:
        return self.marking[place]

    def kind(self, transition: str) -> str:
        return self.lo.transition_kinds[transition]["kind"]

    def _check(self) -> None:
        py = self.game.marking_dict(self.state)
        assert self.marking == py, (self.history, self.marking, py)
        assert self.outcome == self.state.outcome, (self.history, self.outcome, self.state.outcome)

    # ------------------------------------------------------------ steps
    def _dispatch(self, key: tuple, guards: dict[str, bool], label: str) -> set[str]:
        trigger = None
        for t in self.lo.net.transitions:
            if t.trigger == key and t.dispatch in (EVENT, POLLED):
                trigger = self.lo.transition_kinds[t.id]["trigger"]
                if self.lo._uses_oracle(t):
                    self.vm.globals[self.lo.net_name("guard", t.id)] = bool(guards.get(t.id, False))
        assert trigger is not None, f"no trigger for {key}"
        self.vm.run_trigger(trigger)
        self.state = self.game.step(self.state, key, lambda t: bool(guards.get(t.id, False)))
        self.history.append(label)
        self._check()
        return self.marked

    def event(self, transition: str, **guards: bool) -> set[str]:
        """Occurrence of the event of `transition` (all transitions on that
        event are dispatched); world guards default to True for `transition`."""
        t = self.lo.net.transition(transition)
        assert t.dispatch == EVENT, f"{transition} is {t.dispatch}, not an event transition"
        guards = {transition: True, **guards}
        return self._dispatch(t.trigger, guards, f"event {transition}")

    def tick(self, **guards: bool) -> set[str]:
        """One periodic poll tick; world guards are False unless given."""
        return self._dispatch(("poll",), guards, f"tick {guards}")

    def reset(self) -> set[str]:
        self.vm.run_trigger("gt_Reset")
        self.state = self.game.initial()
        self.history.append("reset")
        self._check()
        return self.marked


def dispatch_guard(galaxy: str, transition: str) -> str:
    """The world-guard expression a dispatch trigger evaluates for `transition`
    (the text after `gf_net_en_<t>() &&` in its snapshot line)."""
    import re
    m = re.search(r"lv_c\d+ = \(gf_net_en_" + re.escape(transition) + r"\(\) && (.*)\);\n", galaxy)
    assert m, f"no dispatch guard for {transition}"
    return m.group(1)
