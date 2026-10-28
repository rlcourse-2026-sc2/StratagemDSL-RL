"""A native absent from GUI metadata can still render numeric parameters."""

from types import SimpleNamespace

from stratagemdsl.paths import compiler_root
from stratagemdsl.compiler.galaxycc_adapter import _prepare_imports


def test_fallback_function_text_accepts_numeric_literal_arguments(monkeypatch):
    _prepare_imports(compiler_root())
    from galaxycc.code_gen import FunctionCall, FUNC_DEFS
    monkeypatch.delitem(FUNC_DEFS, "UnitRallyPointTargetPoint", raising=False)
    function = FunctionCall(callee="UnitRallyPointTargetPoint", args=[SimpleNamespace(text=lambda: 1), SimpleNamespace(text=lambda: 2)])
    assert function.text() == "Call self-defined function UnitRallyPointTargetPoint(1, 2)"
