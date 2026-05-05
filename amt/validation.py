"""
AMT SHACL Validation
====================

Thin wrapper around :mod:`pyshacl` that validates an AMT data file against
the bundled ``ontology/amt-shapes.ttl`` and the AMT vocabulary in
``ontology/amt.ttl``.

Two entry points:

* :func:`validate_against_shapes` — returns a structured result dict.
* :func:`AMTValidationError` — raised by :func:`load_amt(..., validate=True)`
  in :mod:`amt.core` when validation fails.
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from pyshacl import validate as _pyshacl_validate

# Default location: the ``ontology/`` folder shipped with the package.
_DEFAULT_ONTOLOGY_DIR = Path(__file__).resolve().parent.parent / "ontology"


class AMTValidationError(Exception):
    """Raised when SHACL validation fails on an AMT data file."""

    def __init__(self, report_text: str, violations: list[dict] | None = None):
        self.report_text = report_text
        self.violations = violations or []
        # Single-line summary plus full report on subsequent lines.
        n = len(self.violations)
        msg = f"SHACL validation failed with {n} violation(s)."
        if violations:
            msg += "\n  " + "\n  ".join(
                f"[{i+1}] {v.get('message', '?')}" for i, v in enumerate(violations)
            )
        super().__init__(msg)


@dataclass
class ValidationResult:
    """Structured result of a SHACL validation run."""

    conforms: bool
    violations: list[dict]
    report_text: str

    def __bool__(self) -> bool:
        return self.conforms


def validate_against_shapes(
    data_source: str | Path,
    *,
    ontology_dir: str | Path | None = None,
) -> ValidationResult:
    """
    Run SHACL validation on a data file (or Turtle string).

    Parameters
    ----------
    data_source
        Either a path to a ``.ttl`` file or a raw Turtle string.
    ontology_dir
        Folder containing ``amt.ttl`` and ``amt-shapes.ttl``. Defaults to
        the bundled ``ontology/`` folder.

    Returns
    -------
    ValidationResult
        With ``conforms`` (bool), ``violations`` (list of dicts with
        ``focus``/``path``/``message`` keys), and the full ``report_text``.
    """
    ont_dir = Path(ontology_dir) if ontology_dir else _DEFAULT_ONTOLOGY_DIR
    shapes = ont_dir / "amt-shapes.ttl"
    ontology = ont_dir / "amt.ttl"

    if not shapes.exists() or not ontology.exists():
        raise FileNotFoundError(
            f"Could not find amt-shapes.ttl and/or amt.ttl in {ont_dir}. "
            "Pass ontology_dir=... or ensure the ontology/ folder is bundled."
        )

    # Resolve data_source: if it's a path that exists, pass it through;
    # otherwise treat it as raw Turtle.
    src_str = str(data_source)
    if Path(src_str).exists():
        data_kwargs = {"data_graph": src_str}
    else:
        data_kwargs = {"data_graph": src_str, "data_graph_format": "turtle"}

    conforms, _report_graph, report_text = _pyshacl_validate(
        shacl_graph=str(shapes),
        ont_graph=str(ontology),
        inference="rdfs",
        advanced=True,  # required for sh:sparql constraints (Hamacher)
        debug=False,
        **data_kwargs,
    )

    violations = _extract_violations(report_text) if not conforms else []
    return ValidationResult(
        conforms=conforms,
        violations=violations,
        report_text=report_text,
    )


def _extract_violations(report_text: str) -> list[dict]:
    """Parse pyshacl's human-readable report into structured violations."""
    out: list[dict] = []
    current: dict | None = None
    for raw in report_text.splitlines():
        line = raw.strip()
        if line.startswith("Constraint Violation"):
            if current is not None:
                out.append(current)
            current = {"focus": "?", "path": "?", "message": "?"}
        elif current is not None:
            if line.startswith("Focus Node:"):
                current["focus"] = line.split(":", 1)[1].strip()
            elif line.startswith("Result Path:"):
                current["path"] = line.split(":", 1)[1].strip()
            elif line.startswith("Message:"):
                current["message"] = line.split(":", 1)[1].strip()
    if current is not None:
        out.append(current)
    return out
