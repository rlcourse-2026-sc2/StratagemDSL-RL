"""The token game: executable semantics of a Strategic Petri Net.

One `TokenGame` serves three clients with the same rules:

* the analysis (`net.analysis`) explores every abstract successor,
* the reference simulator (`simulate`) replays a concrete event trace,
* the differential test checks the generated Galaxy against `simulate`.

Step semantics (the Galaxy backend implements exactly this):

  enabled(t)   not halted; every normal and read input holds >= weight
               tokens; every inhibitor input holds < weight tokens; every
               output place stays within its capacity (an arrival at an
               already-entered `once` place is discarded and needs no room)
  fire(t)      consume normal inputs, run t's actions, produce outputs;
               a place going 0 -> n is *entered* (its `do` block runs),
               n -> 0 is *left* (its timers/revealers stop); under halting the
               first produced terminal latches the outcome and clears the rest
  settle       repeatedly fire the highest-ranked enabled immediate
               transition whose guard holds, until none is enabled
  dispatch     an event occurrence (or a poll tick) takes a snapshot of the
               candidates of that trigger that are enabled and whose guard
               holds, fires them in rank order while each is still enabled,
               then settles. Tokens produced during the dispatch are not
               consumed by the same occurrence.

Rank = (priority, declaration order); lower fires first.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from itertools import combinations
from typing import Callable, Iterable, Optional

from stratagemdsl.net.guards import truth
from stratagemdsl.net.model import EVENT, IMMEDIATE, POLLED, NetTransition, PetriNet

SETTLE_LIMIT = 10_000
OUTCOME = {"success": 1, "failure": 2}


class ZenoError(RuntimeError):
    """Immediate transitions kept firing without reaching a stable marking."""


@dataclass(frozen=True)
class State:
    marking: tuple[int, ...]
    seen: int = 0            # bit i: once-place i has been entered this round
    outcome: int = 0         # 0 running, 1 success, 2 failure (halting nets)


@dataclass
class StepLog:
    fired: list[str] = field(default_factory=list)
    entered: list[str] = field(default_factory=list)
    left: list[str] = field(default_factory=list)
    discarded: list[str] = field(default_factory=list)


class _T:
    """Pre-indexed transition."""
    __slots__ = ("t", "consume", "read", "inhibit", "produce", "id")

    def __init__(self, t: NetTransition, idx: dict[str, int]):
        self.t = t
        self.id = t.id
        self.consume = [(idx[a.place], a.weight) for a in t.inputs if a.kind == "normal"]
        self.read = [(idx[a.place], a.weight) for a in t.inputs if a.kind == "read"]
        self.inhibit = [(idx[a.place], a.weight) for a in t.inputs if a.kind == "inhibit"]
        self.produce = [(idx[a.place], a.weight) for a in t.outputs]


class TokenGame:
    def __init__(self, net: PetriNet):
        self.net = net
        self.places = list(net.places.values())
        self.idx = {p.id: i for i, p in enumerate(self.places)}
        self.cap = [p.capacity for p in self.places]
        self.once = [p.once for p in self.places]
        self.terminal = [OUTCOME.get(p.terminal or "", 0) for p in self.places]
        self.ts = {t.id: _T(t, self.idx) for t in net.transitions}
        ranked = sorted(net.transitions, key=lambda t: t.rank)
        self.immediate = [self.ts[t.id] for t in ranked if t.dispatch == IMMEDIATE]
        self.groups: dict[tuple, list[_T]] = {}
        for t in ranked:
            if t.dispatch in (EVENT, POLLED):
                self.groups.setdefault(t.trigger, []).append(self.ts[t.id])

    # ------------------------------------------------------------ helpers
    def initial(self, log: Optional[StepLog] = None) -> State:
        m = tuple(p.initial for p in self.places)
        seen = 0
        for i, p in enumerate(self.places):
            if p.once and p.initial > 0:
                seen |= 1 << i
        if log is not None:
            log.entered.extend(p.id for p in self.places if p.initial > 0)
        # A terminal listed in `start` does not latch the outcome (v0.2 did
        # not either; strict mode rejects it as E003_TERMINAL_START).
        return self.settle(State(m, seen, 0), log)

    def marking_dict(self, s: State) -> dict[str, int]:
        return {p.id: s.marking[i] for i, p in enumerate(self.places)}

    def marked(self, s: State) -> dict[str, int]:
        return {p.id: s.marking[i] for i, p in enumerate(self.places) if s.marking[i]}

    def guard(self, s: State, t: NetTransition) -> Optional[bool]:
        """Kleene truth of t's guard in s (None: depends on the world)."""
        if t.guard_static is not None:
            return t.guard_static
        return truth(t.guard, self.marking_dict(s), self.net.derived)

    # --------------------------------------------------------- enabling
    def enabled(self, s: State, x: _T) -> bool:
        if s.outcome:
            return False
        m = s.marking
        for i, w in x.consume:
            if m[i] < w:
                return False
        for i, w in x.read:
            if m[i] < w:
                return False
        for i, w in x.inhibit:
            if m[i] >= w:
                return False
        if x.produce:
            for i, w in x.produce:
                if self.once[i] and (s.seen >> i) & 1:
                    continue          # will be discarded
                cap = self.cap[i]
                if cap is None:
                    continue
                after = m[i] - sum(cw for ci, cw in x.consume if ci == i) + w
                if after > cap:
                    return False
        return True

    def capacity_blocked(self, s: State, x: _T) -> bool:
        """Enabled except that an output place is full."""
        if s.outcome or self.enabled(s, x):
            return False
        m = s.marking
        ok = (all(m[i] >= w for i, w in x.consume) and all(m[i] >= w for i, w in x.read)
              and all(m[i] < w for i, w in x.inhibit))
        return ok

    # ------------------------------------------------------------ firing
    def fire(self, s: State, x: _T, log: Optional[StepLog] = None) -> State:
        m = list(s.marking)
        seen = s.seen
        outcome = 0
        for i, w in x.consume:
            m[i] -= w
            if m[i] == 0 and log is not None:
                log.left.append(self.places[i].id)
        for i, w in x.produce:
            if self.once[i]:
                if (seen >> i) & 1:
                    if log is not None:
                        log.discarded.append(self.places[i].id)
                    continue
                seen |= 1 << i
            before = m[i]
            m[i] += w
            if before == 0 and log is not None:
                log.entered.append(self.places[i].id)
            if self.net.halting and self.terminal[i] and not outcome:
                outcome = self.terminal[i]
                for j in range(len(m)):
                    if j != i and m[j]:
                        if log is not None:
                            log.left.append(self.places[j].id)
                        m[j] = 0
                break   # the halt clears every later output too
        if log is not None:
            log.fired.append(x.id)
        return State(tuple(m), seen, outcome)

    def settle(self, s: State, log: Optional[StepLog] = None) -> State:
        for _ in range(SETTLE_LIMIT):
            for x in self.immediate:
                if self.enabled(s, x) and self.guard(s, x.t) is True:
                    s = self.fire(s, x, log)
                    break
            else:
                return s
        raise ZenoError("immediate transitions did not settle")

    def dispatch(self, s: State, selected: Iterable[_T], log: Optional[StepLog] = None) -> State:
        """Fire the snapshot `selected` (already rank ordered), then settle."""
        for x in selected:
            if self.enabled(s, x):
                s = self.fire(s, x, log)
        return self.settle(s, log)

    # --------------------------------------------------- concrete stepping
    def step(self, s: State, trigger: tuple, oracle: Callable[[NetTransition], bool],
             log: Optional[StepLog] = None) -> State:
        """One event occurrence / poll tick with world guards decided by `oracle`."""
        snapshot = []
        for x in self.groups.get(trigger, []):
            if not self.enabled(s, x):
                continue
            g = self.guard(s, x.t)
            if g is None:
                g = bool(oracle(x.t))
            if g:
                snapshot.append(x)
        return self.dispatch(s, snapshot, log)

    # --------------------------------------------------- abstract stepping
    def candidates(self, s: State, trigger: tuple) -> tuple[list[_T], list[_T]]:
        """(guard surely true, guard unknown) enabled candidates of a trigger."""
        sure, maybe = [], []
        for x in self.groups.get(trigger, []):
            if not self.enabled(s, x):
                continue
            g = self.guard(s, x.t)
            if g is True:
                sure.append(x)
            elif g is None:
                maybe.append(x)
        return sure, maybe

    def successors(self, s: State, subset_limit: int = 10):
        """Every (trigger, fired ids, next state) the world can cause from s.

        World guards are free booleans per occurrence; all their combinations
        are explored (exact w.r.t. the step semantics) up to `subset_limit`
        unknown candidates, beyond which only single choices and the full set
        are tried (`truncated` is set).
        """
        out = []
        truncated = False
        for trigger in self.groups:
            sure, maybe = self.candidates(s, trigger)
            if not sure and not maybe:
                continue
            if len(maybe) <= subset_limit:
                choices = [c for r in range(len(maybe) + 1) for c in combinations(maybe, r)]
            else:
                truncated = True
                choices = [()] + [(x,) for x in maybe] + [tuple(maybe)]
            for chosen in choices:
                pick = set(id(x) for x in chosen)
                selected = [x for x in self.groups[trigger] if x in sure or id(x) in pick]
                if not selected:
                    continue
                log = StepLog()
                nxt = self.dispatch(s, selected, log)
                out.append((trigger, tuple(log.fired), nxt, log, tuple(x.id for x in selected)))
        return out, truncated

    def stuck(self, s: State) -> bool:
        """No transition can ever fire from s whatever the world does."""
        if s.outcome:
            return False
        for x in self.ts.values():
            if self.enabled(s, x) and self.guard(s, x.t) is not False:
                return False
        return True


def simulate(net: PetriNet, trace: list[tuple[tuple, dict[str, bool]]]):
    """Replay `trace` = [(trigger, {transition id: world guard value}), ...].

    Returns the list of (State, StepLog) after the initial settle and after
    every step. Missing guard values default to False.
    """
    game = TokenGame(net)
    log = StepLog()
    s = game.initial(log)
    out = [(s, log)]
    for trigger, guards in trace:
        log = StepLog()
        s = game.step(s, trigger, lambda t: guards.get(t.id, False), log)
        out.append((s, log))
    return game, out
