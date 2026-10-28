"""Agents for the allied side: LLM (with or without the plan), scripted opening, idle."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional

from stratagemdsl.core.model import Phase
from stratagemdsl.frontend.unparse import _print_expr
from stratagemdsl.llm.client import _json_from_text
from stratagemdsl.play.actions import MacroAction, parse_actions
from stratagemdsl.play.game import Frame
from stratagemdsl.play.llm import Decider
from stratagemdsl.play.observe import ForceTracker
from stratagemdsl.play.scenario import Scenario

ANSWER_FORMAT = ('{"orders": [{"force": "<force>", "action": "move|attack|hold|retreat", "target": "<name>"}], '
                 '"note": "<one short sentence>"}')


@dataclass
class Decision:
    actions: list[MacroAction]
    calls: list[dict] = field(default_factory=list)    # one per LLM request: prompt, reply, tokens, errors
    errors: list[str] = field(default_factory=list)
    note: str = ""


class Agent:
    name = "agent"

    def reset(self, scenario: Scenario, decision_seconds: float) -> None:
        self.sc = scenario
        self.decision_seconds = decision_seconds

    def decide(self, frame: Frame, tracker: ForceTracker, events: list[dict]) -> Decision:
        return Decision([])


class IdleAgent(Agent):
    """No allied orders: for maps built with --oracle, where the plan itself commands both sides."""
    name = "plan"


class ScriptedAgent(Agent):
    """Fixed orders ("force:action[:target]"): the no-stratagem baseline. They are re-issued at
    every decision, so an attack on a moving enemy force follows its current position."""
    name = "direct"

    def __init__(self, specs: list[str], *, repeat: bool = True):
        self.specs = specs
        self.repeat = repeat
        self._sent = False

    def reset(self, scenario, decision_seconds):
        super().reset(scenario, decision_seconds)
        self._sent = False
        items = []
        for spec in self.specs:
            parts = spec.split(":")
            items.append({"force": parts[0], "action": parts[1] if len(parts) > 1 else "",
                          "target": parts[2] if len(parts) > 2 else None})
        self.actions, errors = parse_actions(items, scenario)
        if errors:
            raise ValueError("; ".join(errors))

    def decide(self, frame, tracker, events):
        if self._sent and not self.repeat:
            return Decision([])
        self._sent = True
        return Decision(list(self.actions))


def default_direct_orders(scenario: Scenario) -> list[str]:
    """Baseline without a stratagem: every allied force attacks the strongest enemy force."""
    enemies = [f for f in scenario.forces.values() if f.side == "enemy" and f.kind == "force"]
    target = max(enemies, key=lambda f: f.count, default=None) or next(
        (f for f in scenario.forces.values() if f.side == "enemy"), None)
    if target is None:
        return []
    return [f"{name}:attack:{target.name}" for name in scenario.controlled]


def plan_brief(scenario: Scenario) -> str:
    """The plan in words, for the `intents` condition: phases, their orders and what moves them on."""
    plan = scenario.strategy.plan
    phases = {n.id: n for n in plan.nodes if isinstance(n, Phase) and not n.terminal}
    side = {f.name: f.side for f in scenario.forces.values()}
    lines = [f"Start: {', '.join(s for s in plan.start if s in phases)}"]
    for pid, ph in phases.items():
        if pid == "failure_watch" or (not ph.actions and not ph.actors):
            continue
        who = ", ".join(f"{a} ({side.get(a, '?')})" for a in ph.actors) or "-"
        acts = "; ".join(_print_expr(a) for a in (ph.actions.actions if ph.actions else []))
        lines.append(f"- phase {pid} [{who}]: {ph.purpose}" + (f" Orders: {acts}." if acts else ""))
        for t in plan.transitions:
            if not any(a.place == pid and a.kind == "normal" for a in t.inputs):
                continue
            terminals = {n.id for n in plan.nodes if isinstance(n, Phase) and n.terminal}
            nxt = ", ".join([a.place for a in t.outputs if a.place in phases or a.place in terminals]
                            + [f"marks {a.place}" for a in t.outputs
                               if a.place not in phases and a.place not in terminals])
            cond = []
            if t.event is not None:
                cond.append(f"on {_print_expr(t.event)}")
            if t.guard is not None:
                cond.append(f"if {_print_expr(t.guard)}")
            acts_t = "; ".join(_print_expr(a) for a in (t.actions.actions if t.actions else []))
            reads = [a.place for a in t.inputs if a.kind == "read"]
            if reads:
                cond.append("once " + ", ".join(reads) + " is marked")
            lines.append(f"    then {nxt or '-'} {' '.join(cond)}".rstrip()
                         + (f" -- this makes: {acts_t}" if acts_t else ""))
    return "\n".join(lines)


def terrain_brief(scenario: Scenario, grid: bool) -> str:
    """The map for an agent: plateaus and the ramps between them (optionally the cell grid)."""
    p = scenario.profile
    lines = [f"Terrain of {p.path.name} ({p.width} x {p.height} cells). Ground units change level only "
             "through ramps; higher level = higher ground (units below cannot see up without vision).",
             "Plateaus:"]
    for rg in p.regions:
        x0, y0, x1, y1 = rg.bbox
        lines.append(f"  {rg.rid}: level {rg.level}, x {x0}..{x1}, y {y0}..{y1}, "
                     f"ramps {', '.join(rg.ramps) or 'none (unreachable on foot)'}")
    lines.append("Ramps:")
    lines += [f"  {rp.rid}: at ({rp.center[0]:g}, {rp.center[1]:g}), joins {' and '.join(rp.joins)}" for rp in p.ramps]
    if grid:
        lines += ["Grid (rows north to south; digits = level, '/' = ramp, '#' = impassable, 'x' = doodad):",
                  p.render_grid()]
    return "\n".join(lines)


def system_prompt(scenario: Scenario, decision_seconds: float, *, with_plan: bool, terrain_grid: bool) -> str:
    p = scenario.profile
    terrain = terrain_brief(scenario, terrain_grid)
    places = [f"- {n}: centre ({l.x:g}, {l.y:g}), radius {l.radius:g}" for n, l in sorted(scenario.regions.items())]
    starts = []
    for f in scenario.forces.values():
        kinds = "/".join(f.unit_types) or "?"
        what = "structure" if f.kind == "asset" else f"{f.count} units"
        where = f"({f.spawn[0]:g}, {f.spawn[1]:g})" if f.spawn else "unknown"
        starts.append(f"- {f.name} ({f.side or '?'}, {what}, {kinds}{', role ' + f.role if f.role else ''}): {where}")
    parts = [
        f"You command the allied side (player {scenario.ally_owner}, {scenario.race('ally')}) in a StarCraft II "
        f"scenario on {p.path.name}. The enemy ({scenario.race('enemy')}) is controlled by the map's script.",
        f"Every {decision_seconds:g} seconds of game time you see the situation and may give new orders. "
        "Orders stay in effect until you replace them. Units fight automatically when enemies are in range.",
        "",
        "Objective",
        f"- You win when: {scenario.objective.get('success', '?')}",
        f"- You lose when: {scenario.objective.get('failure', '?')}",
        "",
        "Orders you can give",
        scenario.vocabulary(),
        "",
        "Named places",
        *places,
        "",
        "Starting positions (x right, y up, in cells)",
        *starts,
        "",
        terrain,
    ]
    if with_plan:
        parts += ["", "Plan for this scenario (a verified stratagem; follow it unless the situation demands otherwise)",
                  plan_brief(scenario)]
    parts += ["", "Answer with JSON only, no prose, in this form:", ANSWER_FORMAT,
              "Give orders only for forces whose orders should change; an empty list keeps all current orders."]
    return "\n".join(parts)


class LLMAgent(Agent):
    """Reacts to text observations; `with_plan` adds the strategy's plan (the `intents` condition)."""

    def __init__(self, decider: Decider, *, with_plan: bool = False, terrain_grid: bool = False, retries: int = 1):
        self.decider = decider
        self.with_plan = with_plan
        self.terrain_grid = terrain_grid
        self.retries = retries
        self.name = "intents" if with_plan else "llm"

    def reset(self, scenario, decision_seconds):
        super().reset(scenario, decision_seconds)
        self.system = system_prompt(scenario, decision_seconds, with_plan=self.with_plan,
                                    terrain_grid=self.terrain_grid)
        self.current: dict[str, tuple[str, int]] = {}
        self.feedback: list[str] = []

    def _user_prompt(self, frame: Frame, tracker: ForceTracker, events: list[dict]) -> str:
        lines = [tracker.describe(frame), "", "Your current orders:"]
        for force in self.sc.controlled:
            if force in self.current:
                text, loop = self.current[force]
                mm, ss = divmod(int(loop / 22.4), 60)
                lines.append(f"- {force}: {text} (since {mm:02d}:{ss:02d})")
            else:
                lines.append(f"- {force}: none")
        if events:
            lines += ["", "Since your last decision:"]
            for e in events:
                mm, ss = divmod(int(e["loop"] / 22.4), 60)
                what = f"{e['event']} {e.get('region', '')}".strip()
                lines.append(f"- {mm:02d}:{ss:02d} {e['force']} {what}")
        if self.feedback:
            lines += ["", "Problems with your previous answer (fix them):", *[f"- {x}" for x in self.feedback]]
        return "\n".join(lines)

    def decide(self, frame, tracker, events):
        decision = Decision([])
        user = self._user_prompt(frame, tracker, events)
        for attempt in range(1 + self.retries):
            reply = self.decider.ask(self.system, user)
            call = {"attempt": attempt, "reply": reply.text, "input_tokens": reply.input_tokens,
                    "output_tokens": reply.output_tokens, "seconds": reply.seconds}
            if attempt == 0:
                call["prompt"] = user
            decision.calls.append(call)
            try:
                obj = _json_from_text(reply.text)
                actions, errors = parse_actions(obj.get("orders", []), self.sc)
                decision.note = str(obj.get("note", ""))[:300]
            except (ValueError, AttributeError) as e:
                actions, errors = [], [f"answer is not the requested JSON: {e}"]
            call["errors"] = errors
            if attempt == 0 or len(errors) < len(decision.errors):
                decision.actions, decision.errors = actions, errors   # keep the best attempt
            if not errors:
                break
            user = user + "\n\nYour answer had problems:\n" + "\n".join(f"- {x}" for x in errors) + \
                "\nAnswer again with corrected JSON only."
        self.feedback = list(decision.errors)
        for a in decision.actions:
            self.current[a.force] = (a.text(), frame.game_loop)
        return decision
