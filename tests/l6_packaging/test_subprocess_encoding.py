"""External tools are read and written as UTF-8 whatever the platform codec is.

On a Chinese Windows the default codec of text-mode subprocess pipes is GBK:
Chinese DOT labels reached Graphviz garbled, and MPQEditor output failed to
decode in the reader threads. The check runs in a child interpreter whose
locale codec is ASCII, which fails the same way.
"""
from __future__ import annotations

import os
import shutil
import subprocess
import sys

import pytest

from stratagemdsl import paths

CHILD = """
import locale
from stratagemdsl.views.plangraph import render_svg
assert locale.getpreferredencoding(False).lower() not in ("utf-8", "utf8")
svg = render_svg('digraph { a [label="\\u56f4\\u9b4f\\u6551\\u8d75"]; }')
assert svg is not None and "\\u56f4\\u9b4f\\u6551\\u8d75" in svg, svg
"""


@pytest.mark.skipif(shutil.which("dot") is None, reason="Graphviz dot not installed")
@pytest.mark.skipif(os.name == "nt", reason="the C locale is how this is forced on POSIX")
def test_graphviz_round_trips_chinese_labels_under_a_non_utf8_locale():
    env = dict(os.environ, LC_ALL="C", LANG="C", PYTHONUTF8="0", PYTHONCOERCECLOCALE="0",
               PYTHONPATH=str(paths.REPO_ROOT / "src") + os.pathsep + os.environ.get("PYTHONPATH", ""))
    done = subprocess.run([sys.executable, "-c", CHILD], capture_output=True, text=True,
                          encoding="utf-8", errors="replace", env=env)
    assert done.returncode == 0, done.stderr
