"""GalaxyLowerer: the Strategy -> MapScript.galaxy compiler.

The class is assembled from one mixin per concern so each part can be read and
debugged on its own:

    state.py        name allocation, discovery passes, helpers used by extensions
    expressions.py  expressions and transition guards
    actions.py      action statements
    events.py       `on` event registrations
    program.py      phase/join state, triggers and the final program text
    extensions.py   per-API lowering for the interaction registry
"""
from __future__ import annotations

from typing import Optional

from stratagemdsl.core.model import Strategy
from stratagemdsl.backend.galaxy.actions import ActionLowering
from stratagemdsl.backend.galaxy.errors import LoweringError
from stratagemdsl.backend.galaxy.events import EventLowering
from stratagemdsl.backend.galaxy.expressions import ExpressionLowering
from stratagemdsl.backend.galaxy.program import ProgramAssembly
from stratagemdsl.backend.galaxy.state import LoweringState


class GalaxyLowerer(ProgramAssembly, EventLowering, ActionLowering, ExpressionLowering, LoweringState):
    """
    Lowers the native StratagemDSL PlanGraph -- compiled to a Petri net by
    `stratagemdsl.net` -- into an *environment Galaxy program* that plays the
    net's token game (see program.py).

    Important policy:
      - allied actions describe expected MARL behavior and are NOT issued by Galaxy,
        unless constructed with oracle=True;
      - enemy actions become Galaxy orders;
      - transitions with observable events become Galaxy triggers;
      - PlanGraph remains the canonical strategic IR; Galaxy receives only the environment
        mechanisms required to make that strategy executable.
    """


def lower_to_galaxy(strategy: Strategy, *, oracle: bool = False) -> tuple[str, list[str]]:
    lowerer = GalaxyLowerer(strategy, oracle=oracle)
    return lowerer.emit(), lowerer.notes


def capability_probe(strategy: Strategy, *, oracle: bool = False) -> Optional[str]:
    """Run the lowerer as a support check for strict validation.

    Returns the reason the strategy cannot be lowered, or None.
    ``oracle`` must match the lowering that will be packed into the map.
    """
    try:
        GalaxyLowerer(strategy, oracle=oracle).emit()
    except (LoweringError, ValueError, TypeError) as exc:
        return str(exc)
    return None
