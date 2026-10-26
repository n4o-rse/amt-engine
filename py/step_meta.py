"""
Step ``meta`` — the five places that state the version must agree.

pyproject.toml, ``amt.__version__``, ``CITATION.cff`` (version and
date-released), ``CHANGELOG.md`` (newest released entry) and the
``RELEASE`` constant in ``amt_dev_utils.py``. A release where one of them
was forgotten is the kind of mistake nobody notices until a citation
carries the wrong number.

Standalone:  python py/step_meta.py
"""
from __future__ import annotations

import re
import sys

try:
    from amt_dev_utils import RELEASE, RELEASE_DATE, ROOT, Report
except ImportError:  # imported as py.step_meta
    from py.amt_dev_utils import RELEASE, RELEASE_DATE, ROOT, Report


def _first(pattern: str, text: str) -> str | None:
    m = re.search(pattern, text, flags=re.MULTILINE)
    return m.group(1) if m else None


def main() -> int:
    rep = Report("meta")
    found: dict[str, str | None] = {}

    pyproject = (ROOT / "pyproject.toml").read_text(encoding="utf-8")
    found["pyproject.toml"] = _first(r'^version\s*=\s*"([^"]+)"', pyproject)

    init = (ROOT / "amt" / "__init__.py").read_text(encoding="utf-8")
    found["amt/__init__.py"] = _first(r'^__version__\s*=\s*"([^"]+)"', init)

    cff_path = ROOT / "CITATION.cff"
    changelog_path = ROOT / "CHANGELOG.md"

    if cff_path.exists():
        cff = cff_path.read_text(encoding="utf-8")
        found["CITATION.cff"] = _first(r'^version:\s*"?([^"\s]+)"?', cff)
        released = _first(r'^date-released:\s*"?(\d{4}-\d{2}-\d{2})"?', cff)
        if released != RELEASE_DATE:
            rep.warn(f"CITATION.cff date-released is {released}, RELEASE_DATE is {RELEASE_DATE}")
    else:
        rep.warn("CITATION.cff is missing")

    if changelog_path.exists():
        log = (changelog_path.read_text(encoding="utf-8"))
        # newest entry that is not [Unreleased]
        found["CHANGELOG.md"] = _first(r"^## \[(\d+\.\d+\.\d+)\]", log)
        entry_date = _first(r"^## \[" + re.escape(RELEASE) + r"\] - (\d{4}-\d{2}-\d{2})", log)
        if entry_date != RELEASE_DATE:
            rep.warn(f"CHANGELOG.md dates {RELEASE} as {entry_date}, RELEASE_DATE is {RELEASE_DATE}")
    else:
        rep.warn("CHANGELOG.md is missing")

    found["py/amt_dev_utils.py"] = RELEASE

    width = max(len(k) for k in found)
    for src, ver in found.items():
        print(f"     {src:<{width}}  {ver}")

    versions = {v for v in found.values() if v}
    if len(versions) > 1 or None in found.values():
        return rep.fail("version mismatch between the files above")
    rep.ok(f"all version sources say {RELEASE}")
    return rep.finish()


if __name__ == "__main__":
    sys.exit(main())
