from __future__ import annotations

from dataclasses import dataclass
from typing import Optional


@dataclass(frozen=True)
class RoleSpec:
    name: str
    type_name: str


@dataclass(frozen=True)
class FactPattern:
    kind: str
    args: tuple[str, ...]


@dataclass(frozen=True)
class CausalObligation:
    source: FactPattern
    target: FactPattern
    relation: str = "causes"  # causes | precedes | eventually
    code: str = "C100_CAUSAL_OBLIGATION"
    message: str = "required causal relation is missing"


@dataclass(frozen=True)
class Link:
    """An edge added with a derived fact. Ends are "new" (the derived fact),
    "event" (the transition's event fact) or a label of the rule's `match`."""
    source: str
    target: str
    evidence: str
    strength: str = "semantic"


@dataclass(frozen=True)
class Derivation:
    fact: FactPattern
    evidence: str
    links: tuple[Link, ...] = ()


@dataclass(frozen=True)
class InterpretationRule:
    """A pattern-specific strategic reading of concrete plan facts.

    The rule looks at each phase (scope "phase"), transition (scope
    "transition") or both (scope "any") of the plan, at the facts its actions
    produced:

    * it fires once for every fact matching the first `match` entry (the
      anchor); each further `match` entry takes the first matching fact of the
      same phase or transition, and the rule does not fire without one;
    * with no `match` entry it fires once per transition whose event matches;
    * `event`, when given, must match the transition's event fact;
    * `distinct` role pairs must be bound to different entities.

    In a FactPattern, "$role" is the entity bound to the role, "_" matches
    anything, and any other string matches itself. A fact may have more
    arguments than the pattern (the pattern constrains a prefix). The rule
    does not fire when a role it mentions is unbound.
    """
    scope: str
    match: tuple[tuple[str, FactPattern], ...] = ()
    event: Optional[FactPattern] = None
    distinct: tuple[tuple[str, str], ...] = ()
    derive: tuple[Derivation, ...] = ()


@dataclass(frozen=True)
class PatternDef:
    name: str
    roles: tuple[RoleSpec, ...]
    distinct_roles: tuple[tuple[str, str], ...] = ()
    obligations: tuple[CausalObligation, ...] = ()
    composed_from: tuple[str, ...] = ()
    description: str = ""
    interpretations: tuple[InterpretationRule, ...] = ()


FEINT = PatternDef(
    name="Feint",
    description="Create a credible threat against a fake target, induce defender relocation, then exploit the real target.",
    roles=(
        RoleSpec("decoy", "Force"),
        RoleSpec("fake_target", "Asset"),
        RoleSpec("defenders", "Force"),
        RoleSpec("main_force", "Force"),
        RoleSpec("real_target", "Asset"),
    ),
    distinct_roles=(("fake_target", "real_target"),),
    composed_from=("Induce", "Redirect", "Exploit"),
    obligations=(
        CausalObligation(
            FactPattern("Threat", ("$decoy", "$fake_target")),
            FactPattern("Relocate", ("$defenders", "$fake_target")),
            code="C101_FEINT_THREAT_TO_RELOCATION",
            message="Feint requires the fake threat to causally induce defender relocation.",
        ),
        CausalObligation(
            FactPattern("Relocate", ("$defenders", "$fake_target")),
            FactPattern("DefenseWeakened", ("$real_target",)),
            code="C102_FEINT_RELOCATION_TO_WEAKENING",
            message="Feint requires defender relocation to create a weakened real objective.",
        ),
        CausalObligation(
            FactPattern("DefenseWeakened", ("$real_target",)),
            FactPattern("Attack", ("$main_force", "$real_target")),
            code="C103_FEINT_WEAKENING_TO_EXPLOIT",
            message="Feint requires the weakened real objective to be exploited by the main force.",
        ),
    ),
    interpretations=(
        # Moving the defenders to the fake target weakens the distinct real target.
        InterpretationRule(
            scope="transition",
            match=(("relocate", FactPattern("Relocate", ("$defenders", "$fake_target"))),),
            distinct=(("fake_target", "real_target"),),
            derive=(Derivation(
                FactPattern("DefenseWeakened", ("$real_target",)),
                "pattern interpretation: defenders relocated away from real target",
                (Link("relocate", "new", "relocation -> weakening interpretation"),)),),
        ),
        # The threat is credible when the decoy's entry directly triggers that move.
        InterpretationRule(
            scope="transition",
            match=(("relocate", FactPattern("Relocate", ("$defenders", "$fake_target"))),),
            event=FactPattern("Enter", ("$decoy",)),
            derive=(Derivation(
                FactPattern("Threat", ("$decoy", "$fake_target")),
                "decoy entry directly triggers defender response",
                (Link("new", "relocate", "threat stimulus -> defender response", "strong"),)),),
        ),
    ),
)

LURE = PatternDef(
    name="Lure",
    description="Induce a defending force to leave an advantageous position, then exploit the exposed objective.",
    roles=(
        RoleSpec("bait", "Force"),
        RoleSpec("enemy", "Force"),
        RoleSpec("stronghold", "Asset"),
        RoleSpec("lure_zone", "Region"),
        RoleSpec("relocation_target", "Region"),
        RoleSpec("strike_force", "Force"),
    ),
    distinct_roles=(("bait", "enemy"),),
    composed_from=("Induce", "Redirect", "Exploit"),
    obligations=(
        CausalObligation(FactPattern("Stimulus", ("$bait", "$enemy")), FactPattern("Relocate", ("$enemy", "$relocation_target")), code="C111_LURE_STIMULUS_TO_RELOCATION", message="Lure requires the bait stimulus to induce enemy relocation."),
        CausalObligation(FactPattern("Relocate", ("$enemy", "$relocation_target")), FactPattern("DefenseWeakened", ("$stronghold",)), code="C112_LURE_RELOCATION_TO_EXPOSURE", message="Lure requires relocation to expose the defended stronghold."),
        CausalObligation(FactPattern("DefenseWeakened", ("$stronghold",)), FactPattern("Attack", ("$strike_force", "$stronghold")), code="C113_LURE_EXPOSURE_TO_EXPLOIT", message="Lure requires exploitation of the exposed stronghold."),
    ),
    interpretations=(
        # The bait's entry directly moves the enemy, which leaves its stronghold.
        InterpretationRule(
            scope="transition",
            match=(("relocate", FactPattern("Relocate", ("$enemy", "$relocation_target"))),),
            event=FactPattern("Enter", ("$bait",)),
            derive=(
                Derivation(FactPattern("Stimulus", ("$bait", "$enemy")),
                           "bait entry directly triggers enemy movement",
                           (Link("new", "relocate", "bait stimulus -> induced response", "strong"),)),
                Derivation(FactPattern("DefenseWeakened", ("$stronghold",)),
                           "bound defender leaves its stronghold for the lure target",
                           (Link("relocate", "new", "relocation -> loss of local defense"),)),
            ),
        ),
    ),
)

INDIRECT_RELIEF = PatternDef(
    name="IndirectRelief",
    description="Threaten a critical rear objective to redirect pressure from a protected target, then intercept.",
    roles=(
        RoleSpec("relief_force", "Force"),
        RoleSpec("pressure_force", "Force"),
        RoleSpec("protected_target", "Asset"),
        RoleSpec("diversion_target", "Asset"),
    ),
    distinct_roles=(("protected_target", "diversion_target"), ("relief_force", "pressure_force")),
    composed_from=("Induce", "Redirect", "Exploit"),
    obligations=(
        CausalObligation(FactPattern("Threat", ("$relief_force", "$diversion_target")), FactPattern("Relocate", ("$pressure_force", "$relief_force")), code="C121_RELIEF_THREAT_TO_REDIRECT", message="IndirectRelief requires the rear threat to redirect the pressure force."),
        CausalObligation(FactPattern("Relocate", ("$pressure_force", "$relief_force")), FactPattern("PressureReduced", ("$protected_target",)), code="C122_RELIEF_REDIRECT_TO_RELIEF", message="IndirectRelief requires redirection to reduce pressure on the protected target."),
        CausalObligation(FactPattern("PressureReduced", ("$protected_target",)), FactPattern("Attack", ("$relief_force", "$pressure_force")), code="C123_RELIEF_TO_INTERCEPT", message="IndirectRelief requires exploitation through interception of the redirected force."),
    ),
    interpretations=(
        # The relief force's entry into the rear turns the pressure force around.
        InterpretationRule(
            scope="transition",
            match=(("relocate", FactPattern("Relocate", ("$pressure_force", "$relief_force"))),),
            event=FactPattern("Enter", ("$relief_force",)),
            derive=(
                Derivation(FactPattern("Threat", ("$relief_force", "$diversion_target")),
                           "rear entry threatens the bound diversion target",
                           (Link("new", "relocate", "rear threat -> pressure-force response", "strong"),)),
                Derivation(FactPattern("PressureReduced", ("$protected_target",)),
                           "pressure force retargets away from the protected target",
                           (Link("relocate", "new", "retargeting -> pressure reduction"),)),
            ),
        ),
    ),
)

COVERT_BYPASS = PatternDef(
    name="CovertBypass",
    description="Conceal movement around a frontal blocker, reach the rear, and attack the real objective.",
    roles=(
        RoleSpec("covert_force", "Force"),
        RoleSpec("blocker", "Force"),
        RoleSpec("rear_region", "Region"),
        RoleSpec("target", "Asset"),
    ),
    distinct_roles=(("covert_force", "blocker"),),
    composed_from=("Conceal", "Exploit"),
    obligations=(
        CausalObligation(FactPattern("Conceal", ("$covert_force",)), FactPattern("Bypass", ("$covert_force", "$blocker", "$rear_region")), code="C131_BYPASS_CONCEAL_TO_REAR", message="CovertBypass requires concealment to enable a route around the blocker."),
        CausalObligation(FactPattern("Bypass", ("$covert_force", "$blocker", "$rear_region")), FactPattern("Attack", ("$covert_force", "$target")), code="C132_BYPASS_REAR_TO_EXPLOIT", message="CovertBypass requires the bypassed force to exploit the rear objective."),
    ),
    interpretations=(
        # Concealment and a move to the rear in the same phase make a bypass.
        InterpretationRule(
            scope="phase",
            match=(("conceal", FactPattern("Conceal", ("$covert_force",))),
                   ("move", FactPattern("Relocate", ("$covert_force", "$rear_region")))),
            derive=(Derivation(
                FactPattern("Bypass", ("$covert_force", "$blocker", "$rear_region")),
                "concealed movement reaches a rear region around the bound blocker",
                (Link("conceal", "new", "concealment enables bypass"),
                 Link("move", "new", "rearward movement completes bypass"))),),
        ),
    ),
)

TRAP = PatternDef(
    name="Trap",
    description="Let the enemy commit to a position, close its way out, then exploit it while it is cut off.",
    roles=(
        RoleSpec("enemy", "Force"),        # the force that is trapped
        RoleSpec("lure", "Any"),           # what the enemy commits to: attacks, moves to or enters it
        RoleSpec("way_out", "Any"),        # the way out that is closed: a gate asset or a choke region
        RoleSpec("trap_force", "Force"),   # who exploits the trap
        RoleSpec("objective", "Entity"),   # what is exploited: the trapped force, or what it no longer covers
    ),
    distinct_roles=(("enemy", "trap_force"),),
    composed_from=("Induce", "Isolate", "Exploit"),
    obligations=(
        CausalObligation(FactPattern("Commit", ("$enemy",)), FactPattern("Isolated", ("$enemy",)),
                         code="C141_TRAP_COMMIT_TO_CLOSURE",
                         message="Trap requires the way out to be closed after the enemy commits."),
        CausalObligation(FactPattern("Isolated", ("$enemy",)), FactPattern("Exploit", ("$objective",)),
                         code="C142_TRAP_CLOSURE_TO_EXPLOIT",
                         message="Trap requires the cut-off enemy to be exploited."),
    ),
    interpretations=(
        # Commitment: the enemy is ordered to engage the lure or to move to it,
        # or the plan observes it entering the lure. The commitment precedes
        # the order or entry that shows it, so a closure later in the same
        # sequence or transition comes after it.
        InterpretationRule(
            scope="any",
            match=(("order", FactPattern("Attack", ("$enemy", "$lure"))),),
            derive=(Derivation(FactPattern("Commit", ("$enemy",)), "enemy ordered to engage the lure",
                               (Link("new", "order", "commitment -> engagement order", "strong"),)),),
        ),
        InterpretationRule(
            scope="any",
            match=(("order", FactPattern("Relocate", ("$enemy", "$lure"))),),
            derive=(Derivation(FactPattern("Commit", ("$enemy",)), "enemy ordered to move to the lure",
                               (Link("new", "order", "commitment -> movement order", "strong"),)),),
        ),
        InterpretationRule(
            scope="transition",
            event=FactPattern("Enter", ("$enemy", "$lure")),
            derive=(Derivation(FactPattern("Commit", ("$enemy",)), "the plan observes the enemy entering the lure",
                               (Link("new", "event", "commitment -> observed entry", "strong"),)),),
        ),
        # Closure: the exit is blocked, or the barrier at the exit is raised
        # ("raised" is the SC2 Supply Depot wall mode).
        InterpretationRule(
            scope="any",
            match=(("close", FactPattern("Block", ("_", "$way_out"))),),
            derive=(Derivation(FactPattern("Isolated", ("$enemy",)), "the way out is blocked",
                               (Link("close", "new", "closure -> enemy cut off"),)),),
        ),
        InterpretationRule(
            scope="any",
            match=(("close", FactPattern("SetMode", ("$way_out", "raised"))),),
            derive=(Derivation(FactPattern("Isolated", ("$enemy",)), "the barrier at the way out is raised",
                               (Link("close", "new", "closure -> enemy cut off"),)),),
        ),
        # Exploitation: the trap force attacks the objective, or the plan
        # reacts to the objective's destruction.
        InterpretationRule(
            scope="any",
            match=(("strike", FactPattern("Attack", ("$trap_force", "$objective"))),),
            derive=(Derivation(FactPattern("Exploit", ("$objective",)), "trap force attacks the objective",
                               (Link("strike", "new", "attack -> exploitation"),)),),
        ),
        InterpretationRule(
            scope="transition",
            event=FactPattern("UnitDied", ("$objective",)),
            derive=(Derivation(FactPattern("Exploit", ("$objective",)), "the plan reacts to the objective's losses",
                               (Link("event", "new", "losses observed -> exploitation"),)),),
        ),
    ),
)

PATTERNS: dict[str, PatternDef] = {
    FEINT.name: FEINT,
    LURE.name: LURE,
    INDIRECT_RELIEF.name: INDIRECT_RELIEF,
    COVERT_BYPASS.name: COVERT_BYPASS,
    TRAP.name: TRAP,
}


# Pattern names the corpus uses that have no causal definition yet. They are
# accepted (some keep legacy lint rules in the validator) but the pattern report
# says NOT CHECKED. Any other undefined name is reported as unknown (C096).
UNCHECKED_PATTERNS: frozenset[str] = frozenset({
    "SacrificeBait", "BorrowedWeapon", "EscapeConcealment", "ForwardDeployment",
    "AssetSubstitution", "ApparentStrengthDeception",
})


def get_pattern(name: Optional[str]) -> Optional[PatternDef]:
    if not name:
        return None
    return PATTERNS.get(name)


def known_pattern_names() -> set[str]:
    return set(PATTERNS) | set(UNCHECKED_PATTERNS)
