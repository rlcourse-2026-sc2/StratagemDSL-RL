"""Run the vendored galaxycc compiler on generated Galaxy source.

galaxycc keeps mutable module-level state; run one strategy per process when
compiling many files (the tools/ runners do this).
"""
from __future__ import annotations

import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

from stratagemdsl import paths


@dataclass
class GalaxyCompileResult:
    judge_ok: bool
    judge_result: object
    trigger_xml: Optional[str] = None
    placed_objects_xml: Optional[str] = None
    trigger_text: Optional[str] = None
    checker: str = "galaxycc"
    diagnostics: list = field(default_factory=list)
    skipped: list = field(default_factory=list)


def _prepare_imports(compiler_root: str | Path):
    root = Path(compiler_root).resolve()
    for p in [root, root / "galaxy_v5"]:
        if str(p) not in sys.path:
            sys.path.insert(0, str(p))
    return root


def compile_galaxy_source(
    source: str,
    compiler_root: str | Path | None = None,
    source_path: str | Path | None = None,
) -> GalaxyCompileResult:
    """Parse, type-check (``judge``) and convert Galaxy source to trigger XML.

    Compiler root layout (default: ``paths.compiler_root()``):
      <root>/galaxy_v5/ANSI-C95_V5.lark   - the Lark grammar
      <root>/galaxy_v5/galaxycc/          - the galaxycc package
      <root>/database/symbol_cache.json   - pre-baked TriggerLibs symbol cache

    The cached include entries are literal strings such as
    "E:/galaxy-compiler/TriggerLibs/NativeLib.galaxy". The backend always emits
    `include "TriggerLibs/NativeLib"` and galaxy_ast.ROOT_DIR defaults to the
    same prefix, so includes resolve from the cache without touching disk.

    ``source_path``, when given, receives a copy of the source.
    """
    root = _prepare_imports(compiler_root if compiler_root is not None else paths.compiler_root())

    galaxycc_dir = root / "galaxy_v5" / "galaxycc"
    grammar = root / "galaxy_v5" / "ANSI-C95_V5.lark"
    cache_folder = root / "database"
    if not galaxycc_dir.is_dir() or not grammar.exists():
        raise FileNotFoundError(
            f"'{root}' is not a galaxycc compiler root: expected {galaxycc_dir} and "
            f"{grammar}. Pass --compiler-root or set STRAT_COMPILER_ROOT."
        )

    from lark import Lark
    from galaxycc.transformer import GalaxyTransformer
    from galaxycc.analyzer import Status, init_judge_parser
    from galaxycc.code_gen import convert_xml, generate_xml

    if source_path is not None:
        source_path = Path(source_path).resolve()
        source_path.parent.mkdir(parents=True, exist_ok=True)
        source_path.write_text(source, encoding="utf-8")

    # Only needed if a top-level #include is NOT already satisfied by the
    # cached symbol table; harmless to set up unconditionally.
    init_judge_parser(str(grammar))

    parser = Lark.open(
        str(grammar),
        parser="earley",
        ambiguity="resolve",
        propagate_positions=True,
        maybe_placeholders=False,
    )
    ast = GalaxyTransformer().transform(parser.parse(source))

    judge_result = ast.judge(path="", load_path=str(cache_folder))
    if judge_result != Status.OK:
        return GalaxyCompileResult(False, judge_result)

    xml_node = convert_xml(ast)
    trigger_xml, placed_objects_xml, trigger_text = generate_xml(xml_node)
    return GalaxyCompileResult(
        True, judge_result,
        trigger_xml=trigger_xml,
        placed_objects_xml=placed_objects_xml,
        trigger_text=trigger_text,
    )
