"""
Shared helpers for the development pipeline (``python main.py``).

This module is *not* part of the installable ``amt`` package. It belongs to
the repository's maintenance tooling: tests, ontology checks, example runs
and the docs sync. Nothing in here changes what ``pip install`` ships.

The values below are the single source of truth for "what release is this"
inside the dev pipeline. No step reads the system clock: dates come from
``RELEASE_DATE`` or from the data, so a rebuild changes a file only when
data or model changed.
"""
from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

# --------------------------------------------------------------------------- #
# Release
# --------------------------------------------------------------------------- #
# Must equal [project].version in pyproject.toml, amt.__version__, the top
# released entry of CHANGELOG.md and ``version`` in CITATION.cff. The ``meta``
# step checks all five against each other.
RELEASE = "0.5.0"
RELEASE_DATE = "2026-10-27"

# --------------------------------------------------------------------------- #
# Paths
# --------------------------------------------------------------------------- #
ROOT = Path(__file__).resolve().parents[1]
EXAMPLES_DIR = ROOT / "examples"
DOCS_DIR = ROOT / "docs"
DOCS_DATA_DIR = DOCS_DIR / "data"
ONTOLOGY_DIR = ROOT / "ontology"
TESTS_DIR = ROOT / "tests"

# ``build/`` is already covered by .gitignore, which is why the pipeline
# report lives here and not in ``dist/``: for this repository ``dist/`` is
# setuptools' wheel output, not a folder of versioned products.
BUILD_DIR = ROOT / "build"
EXAMPLES_OUT_DIR = BUILD_DIR / "examples"
DETERMINISM_DIR = BUILD_DIR / "determinism"


def ensure_dirs() -> None:
    """Create the build folders. Safe to call repeatedly."""
    for d in (BUILD_DIR, EXAMPLES_OUT_DIR, DETERMINISM_DIR):
        d.mkdir(parents=True, exist_ok=True)


# --------------------------------------------------------------------------- #
# Strict mode and warnings
# --------------------------------------------------------------------------- #
def strict() -> bool:
    """True when ``python main.py --strict`` (or ``AMT_DEV_STRICT=1``) is active."""
    return os.environ.get("AMT_DEV_STRICT") == "1"


class Report:
    """Collects warnings; in strict mode any warning makes the step fail."""

    def __init__(self, name: str) -> None:
        self.name = name
        self.warnings: list[str] = []

    def ok(self, msg: str) -> None:
        print(f"OK   {msg}")

    def warn(self, msg: str) -> None:
        self.warnings.append(msg)
        print(f"WARN {msg}")

    def fail(self, msg: str) -> int:
        print(f"FAIL {msg}")
        return 1

    def finish(self) -> int:
        if self.warnings and strict():
            print(f"FAIL {len(self.warnings)} warning(s) treated as errors (--strict)")
            return 1
        return 0


# --------------------------------------------------------------------------- #
# Subprocess helper
# --------------------------------------------------------------------------- #
def child_env(**extra: str) -> dict[str, str]:
    """Environment for child processes: UTF-8 on every platform.

    Without PYTHONIOENCODING, the check marks and arrows the engine prints
    fail at the pipe on Windows, and the traceback talks about codecs
    instead of the actual problem.
    """
    env = dict(os.environ)
    env["PYTHONIOENCODING"] = "utf-8"
    env.update(extra)
    return env


def run_python(args: list[str], *, env_extra: dict[str, str] | None = None) -> int:
    """Run ``python <args>`` in the repository root, streaming its output."""
    cmd = [sys.executable, *args]
    proc = subprocess.run(
        cmd,
        cwd=ROOT,
        env=child_env(**(env_extra or {})),
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    return proc.returncode
