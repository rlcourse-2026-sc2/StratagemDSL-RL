"""Play a generated map: LLM and scripted agents through PySC2 (`strat play`).

The map is built from a strategy (`strat pack ... --gameover`), so a terminal
phase ends the game and every game is one scored episode. An agent controls
the allied forces with the DSL's own movement vocabulary; the plan's Galaxy
token game keeps scripting the enemy side, exactly as for MARL agents.

    scenario.py     forces, assets and regions of the strategy, with coordinates
    game.py         backend-neutral game state (units, frames) and orders
    observe.py      which unit belongs to which force; the text an LLM reads
    actions.py      macro actions (move / attack / hold / retreat) -> orders
    agents.py       LLM (with or without the plan's intents), scripted and idle agents
    llm.py          a small JSON-answer client over the configured LLM provider
    pysc2_backend.py  the real game through PySC2 (raw interface); imported lazily
    toysim.py       a movement-only stand-in for SC2, for tests and --dry-run
    plansim.py      a plan-driven stand-in: the Petri net scripts the enemy, toy combat, ground paths
    worldguards.py  plan guards evaluated on a game state (simulator or observation)
    plantracker.py  the plan's progress as one player can observe it
    unitdata.py     approximate unit numbers for plansim
    llm_pysc2.py    the task bundle for LLM-PySC2 (`strat llm-pysc2`, docs/LLM_PYSC2.md)
    runner.py       the episode loop, JSONL logs and the summary

Conditions for the planning experiment (docs/PLAY.md):
    llm       LLM reacts to observations, knows only the objective and the terrain
    intents   the same, plus the plan's phase intents (agent_intents.json)
    plan      no allied agent: an --oracle map executes the (verified) plan itself
    direct    fixed opening orders, no stratagem (baseline)
"""
