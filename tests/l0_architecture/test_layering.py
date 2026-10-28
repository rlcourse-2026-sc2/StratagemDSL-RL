"""Each layer may import only itself and the layers below it.

This is what makes every layer debuggable in isolation: running layer N never
executes code from layer N+1. Lazy imports inside functions are checked too.
"""
import ast
from pathlib import Path

import pytest

import stratagemdsl

PACKAGE = Path(stratagemdsl.__file__).parent
RANK = {
    "paths": 0, "core": 0,
    "frontend": 1,
    "registry": 2,
    "net": 3,
    "semantics": 4,
    "backend": 5,
    "compiler": 6,
    "packaging": 7,
    "views": 8, "debug": 8,
    "pipeline": 9, "llm": 9, "play": 9,
    "cli": 10,
}


def layer_of(module: str) -> str:
    parts = module.split(".")
    return parts[1] if len(parts) > 1 else ""


def imported_modules(path: Path):
    for node in ast.walk(ast.parse(path.read_text(encoding="utf-8"))):
        if isinstance(node, ast.ImportFrom) and node.module and node.level == 0:
            if node.module == "stratagemdsl":
                yield from (f"stratagemdsl.{a.name}" for a in node.names)
            elif node.module.startswith("stratagemdsl."):
                yield node.module
        elif isinstance(node, ast.Import):
            yield from (a.name for a in node.names if a.name.startswith("stratagemdsl."))


MODULES = sorted(p for p in PACKAGE.rglob("*.py") if "_generated" not in p.parts)


def test_every_package_has_a_rank():
    tops = {p.relative_to(PACKAGE).parts[0].removesuffix(".py") for p in MODULES} - {"__init__"}
    assert tops <= set(RANK), tops - set(RANK)


def test_no_relative_imports():
    offenders = [str(p.relative_to(PACKAGE)) for p in MODULES
                 if any(isinstance(n, ast.ImportFrom) and n.level for n in ast.walk(ast.parse(p.read_text(encoding="utf-8"))))]
    assert not offenders


@pytest.mark.parametrize("path", MODULES, ids=lambda p: str(p.relative_to(PACKAGE)))
def test_module_imports_only_lower_layers(path):
    rel = path.relative_to(PACKAGE).parts
    if rel == ("__init__.py",):
        return
    own = rel[0].removesuffix(".py")
    upward = [m for m in imported_modules(path) if RANK[layer_of(m)] > RANK[own]]
    assert not upward, f"{own} must not import {upward}"
