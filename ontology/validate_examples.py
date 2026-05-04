"""
AMT Ontology Validation Demo
============================

Validates the example TTL files against the AMT ontology and SHACL shapes.

This script is location-agnostic: it works whether you place it in the
project root or inside the ontology/ folder. It auto-detects where the
ontology files live.

Usage from VS Code on Windows:
    1. Place this script either in your project root OR in ontology/.
       Both layouts work:

       Layout A (script in project root):
           your-project/
           |-- validate_examples.py
           +-- ontology/
               |-- amt.ttl
               |-- amt-shapes.ttl
               +-- examples/
                   |-- example-valid.ttl
                   +-- example-invalid.ttl

       Layout B (script inside ontology/):
           your-project/
           +-- ontology/
               |-- validate_examples.py
               |-- amt.ttl
               |-- amt-shapes.ttl
               +-- examples/
                   |-- example-valid.ttl
                   +-- example-invalid.ttl

    2. Open a terminal (Ctrl+oe or Terminal -> New Terminal)
    3. Install dependencies once:
           pip install rdflib pyshacl
    4. Run:
           python validate_examples.py
       Or just press F5 / the green Run button in VS Code.
"""

from __future__ import annotations

import sys
from pathlib import Path

try:
    from pyshacl import validate
except ImportError:
    print("ERROR: pyshacl is not installed.")
    print("Run this in your terminal:  pip install rdflib pyshacl")
    sys.exit(1)


# ---------------------------------------------------------------------------
# Locate the ontology folder. Try common layouts in order:
#   1. Same folder as this script (script lives inside ontology/)
#   2. ./ontology/ subfolder (script lives in project root)
#   3. Parent folder (script lives in a sibling folder of ontology/)
# ---------------------------------------------------------------------------
SCRIPT_DIR = Path(__file__).resolve().parent


def find_ontology_dir() -> Path:
    """
    Try a few sensible locations for the ontology folder. Return the first
    one that contains the expected files.
    """
    candidates = [
        SCRIPT_DIR,  # script is inside ontology/
        SCRIPT_DIR / "ontology",  # script is one level above ontology/
        SCRIPT_DIR.parent,  # script is in a sibling folder
    ]
    for candidate in candidates:
        if (candidate / "amt.ttl").exists() and (candidate / "amt-shapes.ttl").exists():
            return candidate

    print("ERROR: Could not find the ontology folder.")
    print("Looked in these locations for amt.ttl and amt-shapes.ttl:")
    for c in candidates:
        print(f"  - {c}")
    print()
    print("Make sure your folder structure matches one of the layouts")
    print("described at the top of this script.")
    sys.exit(1)


ONTOLOGY_DIR = find_ontology_dir()
ONTOLOGY_TTL = ONTOLOGY_DIR / "amt.ttl"
SHAPES_TTL = ONTOLOGY_DIR / "amt-shapes.ttl"
EXAMPLES_DIR = ONTOLOGY_DIR / "examples"


def check_files_exist() -> None:
    """Make sure example files are present before we do anything."""
    required = [
        EXAMPLES_DIR / "example-valid.ttl",
        EXAMPLES_DIR / "example-invalid.ttl",
    ]
    missing = [str(p) for p in required if not p.exists()]
    if missing:
        print("ERROR: The following example files are missing:")
        for m in missing:
            print(f"  - {m}")
        print()
        print("Expected location:", EXAMPLES_DIR)
        sys.exit(1)


def validate_file(data_file: Path, expected_to_pass: bool) -> bool:
    """
    Validate one data file against the AMT shapes.

    Returns True if the validation outcome matches the expectation,
    False otherwise.
    """
    label = "VALID" if expected_to_pass else "INVALID"
    print()
    print("=" * 72)
    print(f"  Validating {data_file.name}  (expected: {label})")
    print("=" * 72)

    conforms, _, report_text = validate(
        data_graph=str(data_file),
        shacl_graph=str(SHAPES_TTL),
        ont_graph=str(ONTOLOGY_TTL),
        inference="rdfs",
        advanced=True,  # required for SPARQL constraints (Hamacher)
        debug=False,
    )

    test_passed = conforms == expected_to_pass

    if conforms:
        print("  Result: CONFORMS (no violations found)")
    else:
        violations = _extract_violations(report_text)
        print(f"  Result: NOT CONFORMS - {len(violations)} violation(s) found")
        for i, v in enumerate(violations, 1):
            print(f"\n  [{i}] {v['focus']}")
            print(f"      Path:    {v['path']}")
            print(f"      Message: {v['message']}")

    print()
    if test_passed:
        print(
            f"  >> Test result: OK   (expected {label}, got {'VALID' if conforms else 'INVALID'})"
        )
    else:
        print(
            f"  >> Test result: FAIL (expected {label}, got {'VALID' if conforms else 'INVALID'})"
        )

    return test_passed


def _extract_violations(report_text: str) -> list[dict]:
    """Parse the human-readable SHACL report into violation dicts."""
    violations: list[dict] = []
    current: dict | None = None

    for raw_line in report_text.splitlines():
        line = raw_line.strip()

        if line.startswith("Constraint Violation"):
            if current is not None:
                violations.append(current)
            current = {"focus": "?", "path": "?", "message": "?"}
        elif current is not None:
            if line.startswith("Focus Node:"):
                current["focus"] = line.split(":", 1)[1].strip()
            elif line.startswith("Result Path:"):
                current["path"] = line.split(":", 1)[1].strip()
            elif line.startswith("Message:"):
                current["message"] = line.split(":", 1)[1].strip()

    if current is not None:
        violations.append(current)

    return violations


def main() -> int:
    print()
    print("AMT Ontology Validation Demo")
    print("-" * 72)
    print(f"Ontology folder: {ONTOLOGY_DIR}")
    print(f"Ontology:        {ONTOLOGY_TTL.name}")
    print(f"Shapes:          {SHAPES_TTL.name}")

    check_files_exist()

    results = []
    results.append(
        validate_file(EXAMPLES_DIR / "example-valid.ttl", expected_to_pass=True)
    )
    results.append(
        validate_file(EXAMPLES_DIR / "example-invalid.ttl", expected_to_pass=False)
    )

    print()
    print("=" * 72)
    if all(results):
        print("  Summary: ALL TESTS PASSED")
        print("  The valid example conforms; the invalid example fails as")
        print("  expected. The ontology and shapes are working correctly.")
        print("=" * 72)
        return 0
    else:
        print("  Summary: SOME TESTS FAILED")
        print("  Check the output above for details.")
        print("=" * 72)
        return 1


if __name__ == "__main__":
    sys.exit(main())
