"""Shared strategic vocabulary above the SC2 execution layer.

The ontology is deliberately engine-independent.  Pattern definitions refer to
these concepts; :mod:`stratagemdsl.semantics.patterns.facts` grounds them in concrete PlanGraph and
SC2 actions.  This keeps a stratagem name from becoming an opaque validator tag.
"""
from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ConceptSpec:
    name: str
    family: str
    description: str


@dataclass(frozen=True)
class OperatorSpec:
    name: str
    description: str
    typical_effects: tuple[str, ...]


CONCEPTS: dict[str, ConceptSpec] = {
    x.name: x for x in (
        ConceptSpec("Actor", "entity", "An intentional participant or third party."),
        ConceptSpec("Force", "entity", "A controllable military group."),
        ConceptSpec("Asset", "entity", "A valuable, protectable, or attackable object."),
        ConceptSpec("Region", "space", "A strategically meaningful area."),
        ConceptSpec("Route", "space", "A traversable path between regions."),
        ConceptSpec("Capability", "resource", "An action-enabling ability or mode."),
        ConceptSpec("Belief", "epistemic", "What an actor accepts as true."),
        ConceptSpec("Attention", "epistemic", "Where an actor allocates observation or response."),
        ConceptSpec("Suspicion", "epistemic", "Degree of doubt about an apparent state."),
        ConceptSpec("Trust", "epistemic", "Reliance on another actor or signal."),
        ConceptSpec("Strength", "state", "Effective combat power."),
        ConceptSpec("Defense", "state", "Capacity to protect a target."),
        ConceptSpec("Supply", "state", "Sustaining resource flow."),
        ConceptSpec("Mobility", "state", "Capacity to change position."),
        ConceptSpec("Cohesion", "state", "Capacity to act as a coordinated whole."),
        ConceptSpec("Morale", "state", "Willingness to continue an action."),
        ConceptSpec("Dependency", "relation", "A requires B to retain a capability."),
        ConceptSpec("Alliance", "relation", "Actors cooperate toward compatible goals."),
        ConceptSpec("Support", "relation", "One entity sustains another."),
        ConceptSpec("Vulnerability", "opportunity", "A state that can be exploited."),
        ConceptSpec("OpportunityWindow", "opportunity", "A bounded interval for exploitation."),
        ConceptSpec("Risk", "utility", "Expected adverse consequence."),
        ConceptSpec("Cost", "utility", "Resource deliberately spent or exposed."),
        ConceptSpec("Payoff", "utility", "Desired strategic consequence."),
    )
}


OPERATORS: dict[str, OperatorSpec] = {
    x.name: x for x in (
        OperatorSpec("Deceive", "Make an opponent accept an apparent state that differs from reality.", ("Belief", "Attention")),
        OperatorSpec("Conceal", "Prevent observation of an intent, force, route, or action.", ("Belief", "Suspicion")),
        OperatorSpec("Induce", "Create a stimulus that makes another actor choose a response.", ("Attention", "Mobility")),
        OperatorSpec("Redirect", "Move attention, force, or support away from one objective.", ("Attention", "Defense")),
        OperatorSpec("Weaken", "Reduce a capability directly or through a dependency.", ("Strength", "Defense", "Supply")),
        OperatorSpec("Isolate", "Separate an actor from support, allies, or escape routes.", ("Support", "Mobility", "Cohesion")),
        OperatorSpec("Leverage", "Use a third party, terrain, reputation, or captured capability.", ("Capability", "Cost")),
        OperatorSpec("Substitute", "Exchange a lower-value asset for a higher-value outcome.", ("Cost", "Payoff")),
        OperatorSpec("Sacrifice", "Deliberately expose or lose an asset to enable a payoff.", ("Cost", "OpportunityWindow")),
        OperatorSpec("Delay", "Preserve strength while waiting for a favorable condition.", ("Strength", "OpportunityWindow")),
        OperatorSpec("Exploit", "Act on a vulnerability during its opportunity window.", ("Vulnerability", "Payoff")),
        OperatorSpec("Withdraw", "Disengage to preserve force and optionally re-engage later.", ("Strength", "Risk")),
    )
}


def validate_operator_names(names: tuple[str, ...]) -> tuple[str, ...]:
    """Return unknown operator names (stable helper used by tests/tooling)."""
    return tuple(name for name in names if name not in OPERATORS)
