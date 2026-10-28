"""Petri-net IR of a StratagemDSL plan (layer 3).

The PlanGraph written in the DSL is compiled to a *Strategic Petri Net*:

  places       phases, joins (plus their synchronisation places) and `place`
               declarations; every place has a capacity and an initial marking
  transitions  DSL transitions plus the silent synchronisers that implement
               `join` nodes; every transition has input arcs (normal, read,
               inhibitor, with weights) and output arcs (normal, weighted)

Two plan-level rules are kept as place attributes instead of being expanded
into extra places, because the analysis, the simulator and the Galaxy backend
all implement them directly:

  once      an arrival at an already-entered `once` place within one round is
            discarded (the v0.2 "enter a phase at most once" rule)
  halting   with terminal_policy="first_wins" the first terminal place that is
            marked latches the outcome, clears every other place and disables
            every transition

`stratagemdsl.net.pnml.expand_plain` turns both into ordinary P/T structure
(complement places, a halt place and inhibitor arcs) for external tools.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional

from stratagemdsl.core.model import ActionBlock, CallExpr, Expr

# Transition dispatch classes (how the token game decides when to try a firing).
EVENT = "event"          # waits for an SC2 event; guard checked at the event
IMMEDIATE = "immediate"  # fires as soon as it is enabled (eager, priority ordered)
POLLED = "polled"        # no event, live guard: re-checked on the periodic tick

PLACE_KINDS = ("phase", "join", "join_input", "join_arrivals", "join_armed", "resource")


@dataclass
class NetPlace:
    id: str
    kind: str
    origin: str                      # DSL node id this place implements
    initial: int = 0
    capacity: Optional[int] = None   # None: unbounded (analysis must bound it)
    once: bool = False
    terminal: Optional[str] = None   # "success" | "failure" for terminal phases
    label: str = ""

    @property
    def is_control(self) -> bool:
        """A place that stands for a DSL plan node the author wrote."""
        return self.kind in ("phase", "join", "resource")


@dataclass
class NetArc:
    place: str
    weight: int = 1
    kind: str = "normal"   # normal | read | inhibit (inputs); normal (outputs)


@dataclass
class NetTransition:
    id: str
    origin: Optional[str]            # DSL transition id; None for silent transitions
    dispatch: str                    # EVENT | IMMEDIATE | POLLED
    inputs: list[NetArc]
    outputs: list[NetArc]
    priority: int
    order: int                       # declaration order, the priority tie-break
    event: Optional[CallExpr] = None
    guard: Optional[Expr] = None
    actions: Optional[ActionBlock] = None
    silent: bool = False
    trigger: tuple = ()              # transitions with equal trigger race on one dispatch
    guard_static: Optional[bool] = None   # True/False when the guard is a constant
    marking_guard: bool = False      # guard reads only the marking (tokens/active)
    note: str = ""

    @property
    def consumed(self) -> list[str]:
        return [a.place for a in self.inputs if a.kind == "normal"]

    @property
    def rank(self) -> tuple[int, int]:
        return (self.priority, self.order)


@dataclass
class PetriNet:
    name: str
    places: dict[str, NetPlace] = field(default_factory=dict)
    transitions: list[NetTransition] = field(default_factory=list)
    halting: bool = False            # terminal_policy == first_wins
    derived: dict[str, Expr] = field(default_factory=dict)
    notes: list[str] = field(default_factory=list)

    # ------------------------------------------------------------- lookup
    def transition(self, tid: str) -> NetTransition:
        for t in self.transitions:
            if t.id == tid:
                return t
        raise KeyError(tid)

    def by_origin(self, origin: str) -> Optional[NetTransition]:
        return next((t for t in self.transitions if t.origin == origin), None)

    @property
    def place_ids(self) -> list[str]:
        return list(self.places)

    def initial_marking(self) -> dict[str, int]:
        return {p.id: p.initial for p in self.places.values()}

    def terminals(self) -> dict[str, str]:
        return {p.id: p.terminal for p in self.places.values() if p.terminal}

    def producers(self, place: str) -> list[NetTransition]:
        return [t for t in self.transitions if any(a.place == place for a in t.outputs)]

    def consumers(self, place: str) -> list[NetTransition]:
        return [t for t in self.transitions if place in t.consumed]

    def in_conflict(self, a: NetTransition, b: NetTransition) -> bool:
        """Structural conflict: both consume a token from a common place."""
        return a is not b and bool(set(a.consumed) & set(b.consumed))

    def stats(self) -> dict:
        arcs = sum(len(t.inputs) + len(t.outputs) for t in self.transitions)
        kinds: dict[str, int] = {}
        for t in self.transitions:
            kinds[t.dispatch] = kinds.get(t.dispatch, 0) + 1
        return {"places": len(self.places), "transitions": len(self.transitions), "arcs": arcs,
                "silent": sum(t.silent for t in self.transitions), "dispatch": kinds,
                "halting": self.halting}
