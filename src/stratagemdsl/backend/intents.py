"""Export machine-readable allied plan intentions, without claiming execution.

The PyMARL adapter can consume this sidecar alongside the SC2 map. Phase and
transition guards are included as AST objects for downstream translation;
this exporter does not decide an agent policy or a reward function.
"""
from __future__ import annotations

import json

from stratagemdsl.registry.schema import strategy_to_schema_dict
from stratagemdsl.registry.contracts import REGISTRY
from stratagemdsl.core.model import NameExpr, Phase, Strategy


def export_agent_intents(strategy: Strategy) -> dict:
    schema = strategy_to_schema_dict(strategy)
    side = {e.name: e.properties.get("side") for e in strategy.world}
    nodes = {n["id"]: n for n in schema["plan"]["nodes"] if n["node_type"] == "phase"}
    transitions = {t["id"]: t for t in schema["plan"]["transitions"]}

    def allied_actions(block, model_block):
        if not block or not model_block:
            return []
        actions = []
        for index, (action, encoded) in enumerate(zip(model_block.actions, block["actions"])):
            actor = action.args[0].name if action.args and isinstance(action.args[0], NameExpr) else None
            spec = REGISTRY.get(("action", action.name))
            if side.get(actor) == "ally" and spec is not None and "ally -> intent" in spec.actor:
                actions.append({"index": index, "actor": actor, "call": encoded,
                                "status": "strategic_intent_only"})
        return actions

    phase_intents = []
    for phase in strategy.plan.nodes:
        if not isinstance(phase, Phase):
            continue
        n = nodes[phase.id]
        actions = allied_actions(n["actions"], phase.actions)
        if not actions and not any(side.get(actor) == "ally" for actor in phase.actors):
            continue
        phase_intents.append({
            "phase": phase.id, "purpose": phase.purpose,
            "actors": [a for a in phase.actors if side.get(a) == "ally"],
            "focus": phase.focus,
            "actions": {"mode": phase.actions.mode if phase.actions else "none", "items": actions},
            "entry_annotation": n["entry"], "exit_annotation": n["exit"],
            "outgoing_observation": [
                {"transition": t.id, "target": t.target, "event": transitions[t.id]["event"],
                 "guard": transitions[t.id]["guard"]}
                for t in strategy.plan.transitions if phase.id in [a.place for a in t.inputs if a.kind == "normal"]
            ],
        })

    transition_intents = []
    for t in strategy.plan.transitions:
        item = transitions[t.id]
        actions = allied_actions(item["actions"], t.actions)
        if actions:
            transition_intents.append({"transition": t.id, "source": t.source, "target": t.target,
                                       "inputs": [a.place for a in t.inputs if a.kind == "normal"],
                                       "outputs": [a.place for a in t.outputs],
                                       "event": item["event"], "guard": item["guard"],
                                       "actions": {"mode": t.actions.mode, "items": actions}})

    return {
        "format": "stratagemdsl.agent-intents.v1", "strategy": strategy.name,
        "execution": "advisory; Galaxy does not issue allied orders",
        "intent_success": schema["intent"]["success"], "intent_failure": schema["intent"]["failure"],
        "phase_intents": phase_intents, "transition_intents": transition_intents,
    }


def agent_intents_json(strategy: Strategy) -> str:
    return json.dumps(export_agent_intents(strategy), ensure_ascii=False, indent=2) + "\n"
