"""
SimulatedLLM: a deterministic, local stand-in for a hosted LLM completion
call.

This sandbox has no network access to any real LLM provider (OpenAI,
Anthropic, etc. are not reachable), so "calling an LLM" to author new
StratagemDSL variants is implemented here as a seeded generative policy
instead: given a parsed seed Strategy plus a numeric seed, it produces an
"edit plan" -- the same kind of structured decision a real LLM would be
asked to emit if it were prompted with the DSL grammar, the seed source,
and a few-shot style guide of existing hand-authored variants (which is
exactly what a `services.run_stage_planning`-style prompt in smac-ast's own
web app would contain). The plan is then applied to a deep copy of the AST,
never to raw text, so every mutation is type-directed and can only ever
produce grammar-shaped output.

If a real API key becomes available, `SimulatedLLM.propose_variant` is the
single seam to replace with an actual provider call that returns the same
`VariantPlan` shape (parsed from the model's JSON output).
"""
from __future__ import annotations

import copy
import json
import random
from dataclasses import dataclass, field
from typing import Optional

from stratagemdsl.core.model import (
    Strategy, Expr, NameExpr, NumberExpr, CallExpr, UnaryExpr, BinaryExpr,
    BindingCall,
)

# Faction-grouped mobile combat unit pools, mined from the existing corpus
# (examples/ + examples_variants*/). Units tied to a stratagem-specific
# ability (SiegeTank <-> Unsiege, Infestor <-> Neural Parasite, etc.) are
# deliberately left out of the swap pools; those forces are protected
# separately by `_ability_locked_forces` regardless.
UNIT_POOLS: dict[str, list[str]] = {
    "protoss": ["Zealot", "Stalker", "Sentry", "Immortal"],
    "terran": ["Marine", "Hellion", "Medivac"],
    "zerg": ["Zergling", "Roach"],
}
UNIT_TO_FACTION = {u: fac for fac, us in UNIT_POOLS.items() for u in us}


@dataclass
class VariantPlan:
    """The structured decision a (simulated) LLM call returns."""
    name_suffix: str
    theme: str
    scale_factor: float
    radius_factor: float
    threshold_delta: int
    unit_swaps: dict[str, str] = field(default_factory=dict)  # old_type -> new_type
    notes: list[str] = field(default_factory=list)


class SimulatedLLM:
    def __init__(self, seed: int) -> None:
        self.rng = random.Random(seed)
        self.seed = seed

    # ------------------------------------------------------------------
    # "Prompting" step: decide what a variant of this seed should change.
    # Framed as a plan so it is auditable, unlike a raw text diff would be.
    # ------------------------------------------------------------------
    def _plan_variant(self, strategy: Strategy, theme: str) -> VariantPlan:
        scale_factor = round(self.rng.uniform(0.6, 1.6), 2)
        radius_factor = round(self.rng.uniform(0.7, 1.4), 2)
        threshold_delta = self.rng.choice([-2, -1, 1, 1, 2])

        locked = _ability_locked_forces(strategy)
        swap_bound = _bound_unit_types(strategy)
        unit_swaps: dict[str, str] = {}
        for force_name, unit_type in swap_bound.items():
            if force_name in locked:
                continue
            faction = UNIT_TO_FACTION.get(unit_type)
            if faction is None:
                continue
            if self.rng.random() < 0.5:
                pool = [u for u in UNIT_POOLS[faction] if u != unit_type]
                if pool:
                    unit_swaps[unit_type] = self.rng.choice(pool)

        notes = [
            f"scale allied/enemy force sizes by x{scale_factor}",
            f"scale region radii by x{radius_factor}",
            f"shift numeric thresholds by {threshold_delta:+d}",
        ]
        if unit_swaps:
            notes.append("unit swaps: " + ", ".join(f"{k}->{v}" for k, v in unit_swaps.items()))

        suffix = f"{theme}_{self.seed}"
        return VariantPlan(
            name_suffix=suffix,
            theme=theme,
            scale_factor=scale_factor,
            radius_factor=radius_factor,
            threshold_delta=threshold_delta,
            unit_swaps=unit_swaps,
            notes=notes,
        )

    # ------------------------------------------------------------------
    # "Generation" step: apply the plan to a deep copy of the typed AST.
    # ------------------------------------------------------------------
    def propose_variant(self, strategy: Strategy, theme: str) -> tuple[Strategy, VariantPlan]:
        plan = self._plan_variant(strategy, theme)
        out = copy.deepcopy(strategy)
        out.name = f"{strategy.name}_{plan.name_suffix}"

        for b in out.bindings:
            _mutate_binding_value(b.value, plan)

        for d in out.derived:
            _mutate_expr_thresholds(d.expr, plan)
        _mutate_expr_thresholds(out.intent.primary, plan)
        if out.intent.secondary is not None:
            _mutate_expr_thresholds(out.intent.secondary, plan)
        _mutate_expr_thresholds(out.intent.success, plan)
        _mutate_expr_thresholds(out.intent.failure, plan)
        for node in out.plan.nodes:
            if node.__class__.__name__ == "Phase":
                for e in (node.entry, node.invariant, node.exit):
                    if e is not None:
                        _mutate_expr_thresholds(e, plan)
        for t in out.plan.transitions:
            if t.guard is not None:
                _mutate_expr_thresholds(t.guard, plan)

        return out, plan


# ----------------------------------------------------------------------
# Helpers operating on the typed AST (never on raw text).
# ----------------------------------------------------------------------

def _bound_unit_types(strategy: Strategy) -> dict[str, str]:
    """force/asset name -> single unit_type, only when unambiguous
    (skips mixed `composition=[...]` bindings and group_slice aliases,
    which are handled separately during scaling but are not safe/simple
    single-slot swap targets)."""
    out: dict[str, str] = {}
    for b in strategy.bindings:
        if isinstance(b.value, BindingCall) and b.value.name in ("unit_group", "unit"):
            unit_type = None
            for a in b.value.args:
                if a.name == "unit_type" and isinstance(a.value, str):
                    unit_type = a.value
            has_composition = any(a.name == "composition" for a in b.value.args)
            if unit_type and not has_composition:
                out[b.name] = unit_type
    return out


def _ability_locked_forces(strategy: Strategy) -> set[str]:
    """Forces that are the target of a cast/set_mode/ability_(completed|cast)
    action or event anywhere in the plan graph -- their unit type is tied to
    a specific in-game ability and must not be swapped out from under it."""
    locked: set[str] = set()

    def scan_call(c: Optional[CallExpr]):
        if c is None:
            return
        if c.name in ("cast", "set_mode", "ability_completed", "ability_cast") and c.args:
            first = c.args[0]
            if isinstance(first, NameExpr):
                locked.add(first.name)

    for node in strategy.plan.nodes:
        if node.__class__.__name__ == "Phase":
            if node.actions:
                for a in node.actions.actions:
                    scan_call(a)
    for t in strategy.plan.transitions:
        scan_call(t.event)
        if t.actions:
            for a in t.actions.actions:
                scan_call(a)
    return locked


def _scale_int(value: float, factor: float, minimum: int = 1) -> int:
    return max(minimum, round(value * factor))


def _mutate_binding_value(value, plan: VariantPlan) -> None:
    """In-place mutation of a Binding's value tree: scale counts/radii,
    apply unit swaps. Only touches BindingCall nodes (the DSL's function-call
    binding forms); leaves plain literals untouched."""
    if isinstance(value, BindingCall):
        for a in value.args:
            if a.name == "unit_type" and isinstance(a.value, str) and a.value in plan.unit_swaps:
                a.value = plan.unit_swaps[a.value]
            elif a.name == "count" and isinstance(a.value, (int, float)):
                a.value = float(_scale_int(a.value, plan.scale_factor))
            elif a.name == "radius" and isinstance(a.value, (int, float)):
                a.value = round(a.value * plan.radius_factor, 1)
            elif a.name == "composition" and isinstance(a.value, list):
                for item in a.value:
                    _mutate_binding_value(item, plan)
            elif isinstance(a.value, BindingCall):
                _mutate_binding_value(a.value, plan)
            elif isinstance(a.value, list):
                for item in a.value:
                    _mutate_binding_value(item, plan)


_THRESHOLD_FUNCS = {"count", "count_in", "killed_in", "apparent_count", "distance", "strength"}


def _mutate_expr_thresholds(e: Expr, plan: VariantPlan) -> None:
    """In-place: for comparisons like `killed_in(F, R) >= 3`, shift the
    constant side by plan.threshold_delta (never below 1)."""
    if isinstance(e, BinaryExpr):
        if e.op in ("<", "<=", ">", ">=", "==", "!="):
            _maybe_shift_threshold(e, plan)
        _mutate_expr_thresholds(e.left, plan)
        _mutate_expr_thresholds(e.right, plan)
    elif isinstance(e, UnaryExpr):
        _mutate_expr_thresholds(e.operand, plan)
    elif isinstance(e, CallExpr):
        for a in e.args:
            _mutate_expr_thresholds(a, plan)


def _maybe_shift_threshold(cmp_expr: BinaryExpr, plan: VariantPlan) -> None:
    left, right = cmp_expr.left, cmp_expr.right
    target = None
    if isinstance(left, CallExpr) and left.name in _THRESHOLD_FUNCS and isinstance(right, NumberExpr):
        target = right
    elif isinstance(right, CallExpr) and right.name in _THRESHOLD_FUNCS and isinstance(left, NumberExpr):
        target = left
    if target is not None:
        target.value = max(1.0, target.value + plan.threshold_delta)


def dumps_plan(plan: VariantPlan) -> str:
    return json.dumps(
        {
            "name_suffix": plan.name_suffix,
            "theme": plan.theme,
            "scale_factor": plan.scale_factor,
            "radius_factor": plan.radius_factor,
            "threshold_delta": plan.threshold_delta,
            "unit_swaps": plan.unit_swaps,
            "notes": plan.notes,
        },
        indent=2,
    )
