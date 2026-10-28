"""Layer 2: the interaction registry is internally consistent."""
from stratagemdsl.registry import extensions as api
from stratagemdsl.registry.builtins import ACTIONS, EVENT_CONTEXT, EVENTS, FUNCTIONS
from stratagemdsl.registry.contracts import REGISTRY


def test_every_extension_is_published_and_exported():
    for ns, table, shared in (("function", api.FUNCS, FUNCTIONS), ("event", api.EVS, EVENTS),
                              ("action", api.ACTS, ACTIONS)):
        for name in table:
            assert name in shared, name
            assert (ns, name) in REGISTRY, name


def test_action_scopes_are_known_and_rewrites_are_flagged():
    assert {scope for _, scope in api.ACTS.values()} <= {"order", "env", "rewrite"}
    assert api.REWRITE_ACTIONS == {n for n, (_, scope) in api.ACTS.items() if scope == "rewrite"}
    assert api.ALWAYS_EMIT == {n for n, (_, scope) in api.ACTS.items() if scope in ("env", "rewrite")}


def test_event_context_functions_name_real_events():
    known = set(EVENTS) | {"timer"}
    for name, events in api.CTX.items():
        assert events <= known, (name, events - known)
        assert EVENT_CONTEXT[name] >= events


def test_vocabularies_point_at_registered_calls():
    names = set(api.FUNCS) | set(api.EVS) | set(api.ACTS)
    for (name, index), vocab in api.VOCAB.items():
        assert name in names, name
        assert vocab == "side" or len(vocab) > 0
        sigs = api.FUNCS.get(name) or api.EVS.get(name) or api.ACTS[name][0]
        assert any(index < len(s.args) for s in sigs), (name, index)


def test_memory_calls_are_registered():
    names = set(api.FUNCS) | set(api.ACTS)
    assert set(api.MEMORY) <= names
