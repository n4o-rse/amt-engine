"""
Locating the bundled ontology
=============================

``amt.ttl`` and ``amt-shapes.ttl`` live in ``ontology/`` at the repository
root, which is where the ontology README, the diagrams and
``validate_examples.py`` expect them. ``pyproject.toml`` maps that folder
onto the package namespace at build time, so an *installed* copy of AMT
finds them under ``amt/ontology/`` rather than as a top-level ``ontology/``
directory in ``site-packages`` — a name any other distribution could claim.

Both layouts therefore exist in the wild, and this module resolves them in
one place:

1. ``amt/ontology/``      — installed (wheel) layout
2. ``<repo>/ontology/``   — clone or editable install

:func:`ontology_dir` returns the first candidate that actually holds the
files, so a clone and an installed package behave the same.
"""
from __future__ import annotations

from pathlib import Path

__all__ = ["ontology_dir", "ontology_candidates", "REQUIRED_FILES"]

#: Files a directory must contain before we accept it as the ontology folder.
REQUIRED_FILES = ("amt.ttl", "amt-shapes.ttl")

_PACKAGE_DIR = Path(__file__).resolve().parent


def ontology_candidates() -> list[Path]:
    """Return the locations searched, in order, for diagnostics."""
    return [
        _PACKAGE_DIR / "ontology",         # installed layout
        _PACKAGE_DIR.parent / "ontology",  # clone / editable layout
    ]


def ontology_dir() -> Path | None:
    """
    Return the bundled ontology directory, or ``None`` if neither layout
    is present. Callers decide whether a missing ontology is fatal.
    """
    for candidate in ontology_candidates():
        if all((candidate / name).exists() for name in REQUIRED_FILES):
            return candidate
    return None
