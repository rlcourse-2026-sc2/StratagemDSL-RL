"""Debug layer 6: python -m stratagemdsl.packaging STEM_DIR STEM --base-map MAP [-o OUT.SC2Map]

Reads STEM.galaxy, STEM.Triggers.xml and STEM.PlacedObjects.xml from STEM_DIR
(the compiler layer's output), writes them into a copy of the base map and
reads every member back.
"""
import argparse
import json
import sys
from pathlib import Path

from stratagemdsl import paths
from stratagemdsl.packaging import pack_and_verify


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(prog="python -m stratagemdsl.packaging", description=__doc__)
    ap.add_argument("directory")
    ap.add_argument("stem")
    ap.add_argument("--base-map", default=str(paths.base_maps_dir() / "jctq_te.SC2Map"))
    ap.add_argument("-o", "--output")
    ap.add_argument("--stormlib")
    args = ap.parse_args(argv)
    d = Path(args.directory)
    read = lambda suffix: (d / f"{args.stem}{suffix}").read_text(encoding="utf-8")
    out = Path(args.output) if args.output else d / f"{args.stem}.SC2Map"
    result = pack_and_verify(Path(args.base_map), out, read(".galaxy"), read(".Triggers.xml"),
                             read(".PlacedObjects.xml"), args.stormlib)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
