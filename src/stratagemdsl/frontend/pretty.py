"""
Pretty-prints any dataclass tree (i.e. the StratagemDSL Strategy AST from
model.py) using the exact same box-drawing convention as smac-ast's own
Galaxy AST printer (galaxy_v5/galaxycc/galaxy_ast.py: ASTNode._build_lines /
.pretty()) -- so the two AST views in the web app look like the same family
of tool instead of two different styles.

Unlike galaxy_ast.py, this does not need a hand-written `_fields_repr()`
override per node class: every StratagemDSL AST node in model.py is a plain
`@dataclass`, so `dataclasses.fields()` gives the (label, value) pairs for
free, uniformly, for every node type.
"""
from __future__ import annotations

import dataclasses
from typing import Any

_BRANCH = "├── "
_LAST = "└── "
_PIPE = "│   "
_BLANK = "    "


def _node_label(obj: Any) -> str:
    return type(obj).__name__


def _build_lines(obj: Any) -> list[str]:
    if not dataclasses.is_dataclass(obj):
        return [repr(obj)]

    header = _node_label(obj)
    fields = [(f.name, getattr(obj, f.name)) for f in dataclasses.fields(obj)]
    if not fields:
        return [header]

    lines = [header]
    for i, (label, val) in enumerate(fields):
        is_last = i == len(fields) - 1
        connector = _LAST if is_last else _BRANCH
        cont_prefix = _BLANK if is_last else _PIPE

        if val is None:
            lines.append(f"{connector}{label}: <none>")

        elif dataclasses.is_dataclass(val):
            child_lines = _build_lines(val)
            lines.append(f"{connector}{label}: {child_lines[0]}")
            for cl in child_lines[1:]:
                lines.append(cont_prefix + cl)

        elif isinstance(val, list):
            if not val:
                lines.append(f"{connector}{label}: []")
            else:
                lines.append(f"{connector}{label}: ({len(val)} items)")
                for j, item in enumerate(val):
                    last_item = j == len(val) - 1
                    sub_conn = _LAST if last_item else _BRANCH
                    sub_cont = cont_prefix + (_BLANK if last_item else _PIPE)
                    if dataclasses.is_dataclass(item):
                        item_lines = _build_lines(item)
                        lines.append(cont_prefix + sub_conn + item_lines[0])
                        for il in item_lines[1:]:
                            lines.append(sub_cont + il)
                    else:
                        lines.append(cont_prefix + sub_conn + repr(item))

        elif isinstance(val, dict):
            # e.g. EntityDecl.properties
            if not val:
                lines.append(f"{connector}{label}: {{}}")
            else:
                lines.append(f"{connector}{label}: ({len(val)} items)")
                items = list(val.items())
                for j, (k, v) in enumerate(items):
                    last_item = j == len(items) - 1
                    sub_conn = _LAST if last_item else _BRANCH
                    lines.append(cont_prefix + sub_conn + f"{k}: {v!r}")

        else:
            lines.append(f"{connector}{label}: {val!r}")

    return lines


def pretty(strategy_or_node: Any) -> str:
    """Return the box-drawn tree text for any StratagemDSL AST node
    (typically a `model.Strategy` root)."""
    return "\n".join(_build_lines(strategy_or_node))
