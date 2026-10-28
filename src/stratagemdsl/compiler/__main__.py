"""Debug layer 5: python -m stratagemdsl.compiler MAPSCRIPT.galaxy [-o OUT_DIR] [--compiler-root DIR]

Input is Galaxy text (for example the output of ``python -m stratagemdsl.backend``),
so the compiler can be debugged without touching the DSL layers.
"""
import argparse
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

from stratagemdsl.compiler import compile_galaxy_source


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(prog="python -m stratagemdsl.compiler", description=__doc__)
    ap.add_argument("galaxy")
    ap.add_argument("-o", "--out-dir", default=".")
    ap.add_argument("--compiler-root")
    args = ap.parse_args(argv)
    source = Path(args.galaxy)
    result = compile_galaxy_source(source.read_text(encoding="utf-8"), args.compiler_root)
    if not result.judge_ok:
        print(f"[GALAXY JUDGE ERROR] {result.judge_result}")
        return 1
    out = Path(args.out_dir)
    out.mkdir(parents=True, exist_ok=True)
    for suffix, text in (("Triggers.xml", result.trigger_xml), ("PlacedObjects.xml", result.placed_objects_xml),
                         ("TriggerText.txt", result.trigger_text or "")):
        (out / f"{source.stem}.{suffix}").write_text(text, encoding="utf-8")
    ET.fromstring(result.trigger_xml)
    ET.fromstring(result.placed_objects_xml)
    for d in result.diagnostics:
        print(f"[plaxtony] {d}")
    print(f"[OK] checked by {result.checker}; {source.stem}.Triggers.xml / .PlacedObjects.xml in {out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
