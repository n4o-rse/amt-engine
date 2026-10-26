"""
Step ``docs-sync`` — copy ``examples/*.ttl`` to ``docs/data/``.

Local twin of ``.github/workflows/sync-examples-to-docs.yml``, so the
webviewer's sample data can be refreshed (and checked) before a push
instead of only after it. The workflow only fires on pushes that touch
``examples/``; a file that was added while the workflow was not running
stays missing until the next such push.

A copy that changes something is reported as a warning. In ``--strict`` mode
that fails the step, which turns it into a drift check for CI.

Standalone:  python py/step_docs_sync.py
"""
from __future__ import annotations

import filecmp
import shutil
import sys

try:
    from amt_dev_utils import DOCS_DATA_DIR, EXAMPLES_DIR, ROOT, Report
except ImportError:
    from py.amt_dev_utils import DOCS_DATA_DIR, EXAMPLES_DIR, ROOT, Report


def main() -> int:
    rep = Report("docs-sync")
    DOCS_DATA_DIR.mkdir(parents=True, exist_ok=True)
    unchanged = 0
    for src in sorted(EXAMPLES_DIR.glob("*.ttl")):
        dst = DOCS_DATA_DIR / src.name
        if dst.exists() and filecmp.cmp(src, dst, shallow=False):
            unchanged += 1
            continue
        verb = "updated" if dst.exists() else "created"
        shutil.copyfile(src, dst)
        rep.warn(f"{verb} {dst.relative_to(ROOT).as_posix()}")
    rep.ok(f"{unchanged} file(s) already in sync")
    return rep.finish()


if __name__ == "__main__":
    sys.exit(main())
