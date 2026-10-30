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

from ._resources import ontology_candidates, ontology_dir as _bundled_ontology_dir
from .core import is_existing_path


# Hints for the messages of ontology/amt-shapes.ttl: (start of the message, what to do).
# {focus} is replaced by the IRI the violation is about.
_HINTS = [
    ("Each Concept must have at least one rdfs:label",
     "Add  {focus} rdfs:label \"...\" .  If this IRI is not meant to be a concept, check where it is used as "
     "the object of amt:instanceOf: every object of amt:instanceOf counts as a Concept (and amt:Concept itself is not one of yours)."),
    ("Each Role must have at least one rdfs:label",
     "Add  {focus} rdfs:label \"...\" ."),
    ("Each Role must have exactly one rdfs:domain",
     "Add exactly one  {focus} rdfs:domain <Concept> ."),
    ("Each Role must have exactly one rdfs:range",
     "Add exactly one  {focus} rdfs:range <Concept> ."),
    ("Hamacher",
     "Add  {focus} amt:logicParameter \"0.5\"^^xsd:decimal .  (any non-negative number)"),
]


def violation_hint(violation: dict) -> str:
    """What to do about one violation, or an empty string if there is no specific advice."""
    message = violation.get("message", "")
    for start, hint in _HINTS:
        if message.startswith(start) or start in message:
            return hint.format(focus=violation.get("focus", "?"))
    return ""


def format_violations(violations: list[dict], *, indent: str = "  ") -> str:
    """
    Render violations for the terminal: the node they are about first, then the
    message, then the hint if one is known. Without the node ("Each Concept
    must have a label") nobody can tell which of the 200 concepts is meant.
    """
    rows: list[str] = []
    for i, v in enumerate(violations, 1):
        focus = v.get("focus", "?")
        path = v.get("path", "?")
        rows.append(f"{indent}[{i}] {focus}")
        rows.append(f"{indent}    {v.get('message', '?')}" + (f"  (property: {path})" if path not in ("?", "") else ""))
        hint = violation_hint(v)
        if hint:
            rows.append(f"{indent}    -> {hint}")
    return "\n".join(rows)


class AMTValidationError(Exception):
    """Raised when SHACL validation fails on an AMT data file."""

    def __init__(self, report_text: str, violations: list[dict] | None = None):
        self.report_text = report_text
        self.violations = violations or []
        # Single-line summary plus full report on subsequent lines.
        n = len(self.violations)
        msg = f"SHACL validation failed with {n} violation(s)."
        if violations:
            msg += "\n" + format_violations(violations)
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
    if ontology_dir:
        ont_dir = Path(ontology_dir)
    else:
        ont_dir = _bundled_ontology_dir()
        if ont_dir is None:
            searched = ", ".join(str(c) for c in ontology_candidates())
            raise FileNotFoundError(
                "Could not find amt-shapes.ttl and amt.ttl. Looked in: "
                f"{searched}. Pass ontology_dir=... or ensure the "
                "ontology/ folder is bundled."
            )
    shapes = ont_dir / "amt-shapes.ttl"
    ontology = ont_dir / "amt.ttl"

    if not shapes.exists() or not ontology.exists():
        raise FileNotFoundError(
            f"Could not find amt-shapes.ttl and/or amt.ttl in {ont_dir}."
        )

    # Resolve data_source: if it's a path that exists, pass it through;
    # otherwise treat it as raw Turtle.
    src_str = str(data_source)
    if is_existing_path(src_str):
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
    # pyshacl reports results in an order that changes from run to run; sort so
    # that messages, reports and tests see the same order every time.
    out.sort(key=lambda v: (v["focus"], v["path"], v["message"]))
    return out
