"""Layer 3: the plan as a Strategic Petri Net.

    build_net(strategy)  -> PetriNet      desugar phases/joins/places/arcs
    analyze(net)         -> NetReport     reachability-based structural proofs
    TokenGame(net)                        executable step semantics
    to_pnml(net)                          ISO/IEC 15909-2 interchange
"""
from stratagemdsl.net.analysis import NetReport, analyze
from stratagemdsl.net.build import build_net, event_signature, terminal_policy
from stratagemdsl.net.model import EVENT, IMMEDIATE, POLLED, NetArc, NetPlace, NetTransition, PetriNet
from stratagemdsl.net.semantics import State, StepLog, TokenGame, simulate

__all__ = ["EVENT", "IMMEDIATE", "POLLED", "NetArc", "NetPlace", "NetReport", "NetTransition", "PetriNet",
           "State", "StepLog", "TokenGame", "analyze", "build_net", "event_signature", "simulate", "terminal_policy"]
