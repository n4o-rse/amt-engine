"""
Step ``docs-sync`` — copy ``examples/*.ttl`` to ``docs/data/`` and list them.

``docs/data/examples.json`` names every example with a title (the text after
``AMT data file:`` in its header comment, else the file name); the Explorer
builds its example list from it.

Local twin of ``.github/workflows/sync-examples-to-docs.yml``, so the
webviewer's sample data can be refreshed (and checked) before a push
instead of only after it. The workflow only fires on pushes that touch
``examples/``; a file that was added while the workflow was not running
stays missing until the next such push.

Files are compared with line endings normalised (CRLF counts as LF). With
``core.autocrlf`` on Windows the same blob appears as CRLF in one working tree
and as LF in another; a byte comparison would report drift where the content
is identical and rewrite files for nothing.

A copy that changes something is reported as a warning. In ``--strict`` mode
that fails the step, which turns it into a drift check for CI.

Standalone:  python py/step_docs_sync.py
"""
from __future__ import annotations

import json
import re
import shutil
import sys
from pathlib import Path

try:
    from amt_dev_utils import DOCS_DATA_DIR, EXAMPLES_DIR, ROOT, Report
except ImportError:
    from py.amt_dev_utils import DOCS_DATA_DIR, EXAMPLES_DIR, ROOT, Report


def _same_content(a: Path, b: Path) -> bool:
    """True when both files hold the same text, ignoring CRLF versus LF."""
    return a.read_bytes().replace(b"\r\n", b"\n") == b.read_bytes().replace(b"\r\n", b"\n")


def example_title(path: Path) -> str:
    """Title of an example: the ``AMT data file: <title>`` header line, else the file stem."""
    for line in path.read_text(encoding="utf-8").splitlines()[:40]:
        m = re.match(r"#\s*AMT data file:\s*(.+?)\s*$", line)
        if m:
            return m.group(1)
    return path.stem


def example_list() -> list[dict]:
    return [{"file": p.name, "title": example_title(p)} for p in sorted(EXAMPLES_DIR.glob("*.ttl"))]


def main() -> int:
    rep = Report("docs-sync")
    DOCS_DATA_DIR.mkdir(parents=True, exist_ok=True)
    unchanged = 0
    for src in sorted(EXAMPLES_DIR.glob("*.ttl")):
        dst = DOCS_DATA_DIR / src.name
        if dst.exists() and _same_content(src, dst):
            unchanged += 1
            continue
        verb = "updated" if dst.exists() else "created"
        shutil.copyfile(src, dst)
        rep.warn(f"{verb} {dst.relative_to(ROOT).as_posix()}")
    listing = (json.dumps(example_list(), indent=2, ensure_ascii=False) + "\n").encode("utf-8")
    manifest = DOCS_DATA_DIR / "examples.json"
    if manifest.exists() and manifest.read_bytes().replace(b"\r\n", b"\n") == listing:
        unchanged += 1
    else:
        verb = "updated" if manifest.exists() else "created"
        manifest.write_bytes(listing)
        rep.warn(f"{verb} {manifest.relative_to(ROOT).as_posix()}")
    rep.ok(f"{unchanged} file(s) already in sync")
    return rep.finish()


if __name__ == "__main__":
    sys.exit(main())
