"""Print a .strat file as the AST classes in core.model.

Run from the StratagemDSL directory:

    python tools/show_ast.py
    python tools/show_ast.py examples/learning/02_join_and_counter.strat
    python tools/show_ast.py --emit examples/learning/02_join_and_counter.strat
    python tools/show_ast.py --emit-dir tests/l0_architecture/cases examples/learning/*.strat
    python tools/show_ast.py --refresh tests/l0_architecture/cases
    python tools/show_ast.py --tree both examples/learning/02_join_and_counter.strat

``--emit`` prints a pytest function whose ``strategy`` object is the same tree
``parse_file`` built. Fields that still hold their dataclass default are left
out. Assertions beyond ``strategy.name`` are not generated.

``--tree`` prints the grammar parse tree, indented like the Lark editor and
ANTLR Lab: rule names on branches, source tokens on leaves. That tree is the
input to the Strategy transform, not the Strategy itself.
"""
import argparse
import glob
import sys
from dataclasses import MISSING, fields, is_dataclass
from pathlib import Path

from stratagemdsl.core.model import (
    ActionBlock,
    BinaryExpr,
    BindingCall,
    BoolExpr,
    CallExpr,
    Join,
    NameExpr,
    NumberExpr,
    StringExpr,
    UnaryExpr,
)
from stratagemdsl.frontend import parse_file
from stratagemdsl.frontend.antlr_parser import parse_document
from stratagemdsl.frontend.lark_parser import parse_tree
from stratagemdsl.paths import REPO_ROOT

DEFAULTS = (
    REPO_ROOT / "examples/learning/02_join_and_counter.strat",
    REPO_ROOT / "examples/learning/03_typed_feint.strat",
)


def brief(e):
    if e is None:
        return "None"
    if isinstance(e, NameExpr):
        return e.name
    if isinstance(e, BoolExpr):
        return str(e.value).lower()
    if isinstance(e, NumberExpr):
        return str(e.value)
    if isinstance(e, StringExpr):
        return repr(e.value)
    if isinstance(e, CallExpr):
        return e.name + "(" + ", ".join(brief(a) for a in e.args) + ")"
    if isinstance(e, UnaryExpr):
        return e.op + " " + brief(e.operand)
    if isinstance(e, BinaryExpr):
        return "(" + brief(e.left) + " " + e.op + " " + brief(e.right) + ")"
    if isinstance(e, ActionBlock):
        body = "; ".join(brief(a) for a in e.actions)
        return e.mode + " { " + body + " }"
    if isinstance(e, BindingCall):
        parts = []
        for a in e.args:
            parts.append((a.name + "=" if a.name else "") + brief_val(a.value))
        return e.name + "(" + ", ".join(parts) + ")"
    return type(e).__name__


def brief_val(v):
    if isinstance(v, BindingCall):
        return brief(v)
    if isinstance(v, str):
        return repr(v)
    if isinstance(v, list):
        return "[" + ", ".join(brief_val(x) for x in v) + "]"
    return str(v)


def show(path):
    s = parse_file(path)
    print("=" * 72)
    print("Strategy", s.name, "backend=", s.backend)
    print("world:")
    for ent in s.world:
        print(" ", ent.kind, ent.name, ent.properties)
    print("intent pattern=", s.intent.pattern, "bindings=", s.intent.pattern_bindings)
    print("  primary  ", brief(s.intent.primary))
    print("  secondary", brief(s.intent.secondary))
    print("  success  ", brief(s.intent.success))
    print("  failure  ", brief(s.intent.failure))
    print("derived:")
    for d in s.derived:
        print(" ", d.name, "=", brief(d.expr))
    print("plan start", s.plan.start)
    for n in s.plan.nodes:
        if isinstance(n, Join):
            print("  JOIN", n.id, "policy=", n.policy, "quorum=", n.quorum)
        else:
            extra = []
            if n.actors:
                extra.append("actors=" + str(n.actors))
            if n.focus:
                extra.append("focus=" + str(n.focus))
            if n.terminal:
                extra.append("terminal=" + n.terminal)
            if n.actions:
                extra.append(brief(n.actions))
            print("  PHASE", n.id, "|", n.purpose, "|", " ".join(extra))
    for t in s.plan.transitions:
        print("  EDGE", t.id, t.source, "->", t.target, "prio", t.priority)
        print("       on   ", brief(t.event))
        print("       when ", brief(t.guard))
        print("       do   ", brief(t.actions))
    print("bindings:")
    for b in s.bindings:
        print(" ", b.name, "=", brief_val(b.value))


def _keeps_default(field, value):
    if field.default is not MISSING:
        return value == field.default
    if field.default_factory is not MISSING:
        return value == field.default_factory()
    return False


def emit(obj, level=0):
    """Python source that rebuilds ``obj``. ``level`` is the indent of its closing line."""
    if obj is None or isinstance(obj, (bool, int, float, str)):
        return repr(obj)
    if isinstance(obj, list):
        return _emit_items(obj, level, "[", "]")
    if isinstance(obj, dict):
        return _emit_dict(obj, level)
    if not is_dataclass(obj):
        raise TypeError(f"cannot emit {type(obj).__name__}")
    pairs = []
    for field in fields(obj):
        value = getattr(obj, field.name)
        if _keeps_default(field, value):
            continue
        pairs.append((field.name, emit(value, level + 1)))
    name = type(obj).__name__
    if not pairs:
        return name + "()"
    one_line = name + "(" + ", ".join(f"{key}={value}" for key, value in pairs) + ")"
    if "\n" not in one_line and len(one_line) <= 88:
        return one_line
    pad_field = "    " * (level + 1)
    pad_close = "    " * level
    body = ",\n".join(f"{pad_field}{key}={value}" for key, value in pairs)
    return f"{name}(\n{body},\n{pad_close})"


def _emit_items(items, level, open_ch, close_ch):
    rendered = [emit(item, level + 1) for item in items]
    if not rendered:
        return open_ch + close_ch
    one_line = open_ch + ", ".join(rendered) + close_ch
    if "\n" not in one_line and len(one_line) <= 60:
        return one_line
    pad_field = "    " * (level + 1)
    pad_close = "    " * level
    body = ",\n".join(pad_field + item for item in rendered)
    return f"{open_ch}\n{body},\n{pad_close}{close_ch}"


def _emit_dict(obj, level):
    if not obj:
        return "{}"
    rendered = [repr(key) + ": " + emit(value, level + 1) for key, value in obj.items()]
    one_line = "{" + ", ".join(rendered) + "}"
    if "\n" not in one_line and len(one_line) <= 60:
        return one_line
    pad_field = "    " * (level + 1)
    pad_close = "    " * level
    body = ",\n".join(pad_field + item for item in rendered)
    return "{\n" + body + ",\n" + pad_close + "}"


def used_classes(obj, found=None):
    if found is None:
        found = set()
    if is_dataclass(obj):
        found.add(type(obj).__name__)
        for field in fields(obj):
            used_classes(getattr(obj, field.name), found)
    elif isinstance(obj, list):
        for item in obj:
            used_classes(item, found)
    elif isinstance(obj, dict):
        for item in obj.values():
            used_classes(item, found)
    return found


def _snake(name):
    out = []
    for i, ch in enumerate(name):
        if ch.isupper() and i and (not name[i - 1].isupper() or (i + 1 < len(name) and name[i + 1].islower())):
            out.append("_")
        out.append(ch.lower())
    return "".join(out)


def case_filename(path: Path) -> str:
    """Stable file name for a case, unique across examples/ and corpus/."""
    try:
        relative = path.resolve().relative_to(REPO_ROOT)
    except ValueError:
        relative = Path(path.name)
    return relative.with_suffix(".py").as_posix().replace("/", "__")


def case_module(strategy, source: Path) -> str:
    """A Python module that rebuilds ``strategy``. Executing it binds ``strategy``."""
    try:
        relative = source.resolve().relative_to(REPO_ROOT).as_posix()
    except ValueError:
        relative = source.as_posix()
    header = "from stratagemdsl.core.model import " + ", ".join(sorted(used_classes(strategy)))
    rendered = emit(strategy, 0)
    lines = rendered.split("\n")
    body = "strategy = " + lines[0]
    if len(lines) > 1:
        body += "\n" + "\n".join(lines[1:])
    return f"# source: {relative}\n{header}\n\n{body}\n"


def write_cases(paths, directory: Path) -> list[Path]:
    directory.mkdir(parents=True, exist_ok=True)
    written = []
    for path in paths:
        destination = directory / case_filename(path)
        destination.write_text(case_module(parse_file(path), path), encoding="utf-8")
        written.append(destination)
    return written


def refresh_cases(directory: Path) -> tuple[list[Path], list[Path], list[str]]:
    """Rewrite every case in ``directory`` from the source named in its header.

    Returns (rewritten, unchanged, missing sources)."""
    rewritten, unchanged, missing = [], [], []
    for case in sorted(directory.glob("*.py")):
        first = case.read_text(encoding="utf-8").split("\n", 1)[0]
        if not first.startswith("# source: "):
            continue
        source = REPO_ROOT / first.removeprefix("# source: ").strip()
        if not source.is_file():
            missing.append(first.removeprefix("# source: ").strip())
            continue
        text = case_module(parse_file(source), source)
        if text == case.read_text(encoding="utf-8"):
            unchanged.append(case)
        else:
            case.write_text(text, encoding="utf-8")
            rewritten.append(case)
    return rewritten, unchanged, missing


def case_source(strategy):
    """A pytest function that rebuilds ``strategy``."""
    header = "from stratagemdsl.core.model import " + ", ".join(sorted(used_classes(strategy)))
    rendered = emit(strategy, 1)
    lines = rendered.split("\n")
    body = "    strategy = " + lines[0]
    if len(lines) > 1:
        body += "\n" + "\n".join(lines[1:])
    body += f"\n    assert strategy.name == {strategy.name!r}"
    return (
        "# Generated by tools/show_ast.py --emit. Add assertions for the behavior under test.\n"
        + header
        + "\n\n"
        + f"def test_{_snake(strategy.name)}():\n"
        + body
        + "\n"
    )


def antlr_tree(source: str) -> str:
    """Indented ANTLR rule tree. Leaves are the source tokens, except EOF."""
    tree, parser = parse_document(source)
    lines = []

    def walk(node, indent):
        if node.getChildCount() == 0:
            text = node.getText()
            if text != "<EOF>":
                lines.append("  " * indent + text)
            return
        lines.append("  " * indent + parser.ruleNames[node.getRuleIndex()])
        for index in range(node.getChildCount()):
            walk(node.getChild(index), indent + 1)

    walk(tree, 0)
    return "\n".join(lines)


def lark_tree(source: str) -> str:
    """Indented Lark rule tree, the same text Tree.pretty() shows in the editor."""
    return parse_tree(source).pretty().rstrip("\n")


def show_parse_trees(path: Path, which: str) -> None:
    source = path.read_text(encoding="utf-8")
    chosen = ("lark", "antlr") if which == "both" else (which,)
    for index, kind in enumerate(chosen):
        if index:
            print()
        print(f"===== {kind} parse tree: {path} =====")
        try:
            rendered = lark_tree(source) if kind == "lark" else antlr_tree(source)
        except SyntaxError as exc:
            print(exc)
            continue
        print(rendered)


def expand_paths(paths):
    """Expand ``*`` patterns. PowerShell often passes them through unexpanded."""
    found = []
    for path in paths:
        text = str(path)
        if any(ch in text for ch in "*?["):
            found.extend(Path(match) for match in sorted(glob.glob(text, recursive=True)))
        else:
            found.append(path)
    return found


def main(argv=None):
    parser = argparse.ArgumentParser(description="Print a .strat AST, or emit a test that rebuilds it.")
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--emit", action="store_true", help="print constructor source for a unit test")
    mode.add_argument("--emit-dir", type=Path, metavar="DIR", help="write one case .py per input into DIR")
    mode.add_argument("--refresh", type=Path, metavar="DIR",
                      help="rewrite every case in DIR from the .strat named in its '# source:' line")
    mode.add_argument(
        "--tree",
        choices=("lark", "antlr", "both"),
        help="print the grammar parse tree (lark, antlr, or both)",
    )
    parser.add_argument("paths", nargs="*", type=Path, help="defaults to the two learning examples")
    args = parser.parse_args(argv)
    if args.refresh:
        rewritten, unchanged, missing = refresh_cases(args.refresh)
        for case in rewritten:
            print(f"rewrote {case}")
        for source in missing:
            print(f"source missing, case left as is: {source}")
        print(f"{len(rewritten)} rewritten, {len(unchanged)} unchanged, {len(missing)} with a missing source")
        return
    paths = expand_paths(args.paths) if args.paths else list(DEFAULTS)
    if not paths:
        parser.error("no input files matched")
    if args.emit_dir:
        for destination in write_cases(paths, args.emit_dir):
            print(destination)
        return
    for index, path in enumerate(paths):
        if args.tree:
            if index:
                print()
            show_parse_trees(path, args.tree)
            continue
        if not args.emit:
            show(path)
            continue
        if index:
            print()
        print(case_source(parse_file(path)), end="")


if __name__ == "__main__":
    main(sys.argv[1:])
