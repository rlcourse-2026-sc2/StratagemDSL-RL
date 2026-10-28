"""StratagemDSL: a strategy language compiled to StarCraft II Galaxy triggers.

Layers (each only imports the ones above it in this list):

    core       AST data model and diagnostics
    frontend   .strat text -> AST
    registry   API signatures, vocabularies, contracts, interchange schema
    net        plan -> Strategic Petri Net, token-game semantics, reachability analysis, PNML
    semantics  type/scope/structure checks, net diagnostics, strategic patterns, strict SC2 checks
    backend    Petri net -> Galaxy MapScript token game (+ allied agent-intent sidecar)
    compiler   Galaxy checks (galaxycc + plaxtony) -> Triggers.xml / PlacedObjects.xml
    packaging  Galaxy + XML -> .SC2Map (StormLib)

``views`` (PlanGraph), ``llm`` (optional generation) and ``pipeline`` / ``cli``
sit on top and combine the layers.
"""
__version__ = "0.6.0"
