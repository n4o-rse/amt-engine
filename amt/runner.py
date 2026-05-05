"""
AMT Runner
==========

Convenience wrapper that runs the full pipeline on one input file:

* validate (optional, default: on)
* load
* print summary + ontology info
* consistency check
* reasoning
* export TTL, Cypher, CSV, HTML

Usable as a library function (``run_all``) or as
``python -m amt.runner input.ttl``.

Output files are placed next to the input by default, under ``out/`` and
named after the input stem::

    examples/Potter.ttl
        -> out/Potter.reasoned.ttl
        -> out/Potter.cypher
        -> out/Potter.csv/         (folder containing nodes.csv + edges.csv)
        -> out/Potter.html
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

from . import (
    AMTValidationError,
    check_consistency,
    do_reasoning,
    export_csv,
    export_cypher,
    export_ttl,
    load_amt,
    local_name,
    render_to_html,
    validate_against_shapes,
)


def run_all(
    input_path: str | Path,
    output_dir: str | Path | None = None,
    *,
    validate: bool = True,
    reason: bool = True,
    check: bool = True,
    info: bool = True,
    export_ttl_: bool = True,
    export_cypher_: bool = True,
    export_csv_: bool = True,
    export_html_: bool = True,
    height: str = "600px",
    ontology_dir: str | Path | None = None,
) -> dict:
    """
    Run the full AMT pipeline. Returns the loaded ``amt`` dict so callers
    (notebook, tests) can keep working with it.
    """
    input_path = Path(input_path)
    if not input_path.exists():
        raise FileNotFoundError(input_path)

    out_dir = Path(output_dir) if output_dir else input_path.parent / "out"
    # Clear the output directory before writing — keeps it tidy across runs
    # and prevents stale files from confusing the user. We only delete the
    # *contents*, not the directory itself, so editor tabs pointing at the
    # folder don't lose their reference.
    if out_dir.exists():
        import shutil
        for entry in out_dir.iterdir():
            if entry.is_dir():
                shutil.rmtree(entry)
            else:
                entry.unlink()
    out_dir.mkdir(parents=True, exist_ok=True)
    stem = input_path.stem

    if validate:
        print(f"VAL  Validating {input_path.name} ...")
        result = validate_against_shapes(input_path, ontology_dir=ontology_dir)
        if not result.conforms:
            print(f"FAIL Validation failed with {len(result.violations)} violation(s):")
            for i, v in enumerate(result.violations, 1):
                print(f"  [{i}] {v.get('message', '?')}")
            raise AMTValidationError(result.report_text, result.violations)
        print("OK   Validation passed.")

    print(f"LOAD Loading {input_path} ...")
    ont_path = (Path(ontology_dir) / "amt.ttl") if ontology_dir else None
    amt = load_amt(input_path, ontology_path=ont_path)
    print(
        f"OK   {len(amt['concepts'])} Concepts | "
        f"{len(amt['roles'])} Roles | "
        f"{len(amt['nodes'])} Nodes | "
        f"{len(amt['edges'])} Edges | "
        f"{len(amt['axioms'])} Axioms"
    )

    if info:
        print("\n== Concepts ==")
        for c in amt["concepts"].values():
            print(f"  - {local_name(c['iri']):20s}  {c['label']}")
        print("\n== Roles ==")
        for r in amt["roles"].values():
            print(
                f"  - {local_name(r['iri']):20s}  "
                f"{local_name(r['domain'])} -> {local_name(r['range'])}"
            )
        print("\n== Axioms ==")
        for a in amt["axioms"]:
            details = {}
            for k, v in a.items():
                if k in ("type", "iri"):
                    continue
                if isinstance(v, list):
                    details[k] = [local_name(x) for x in v]
                else:
                    details[k] = (
                        local_name(v) if isinstance(v, str) and v.startswith("http") else v
                    )
            print(f"  - {a['type']:20s}  {details}")

    if check:
        ok, violations = check_consistency(amt["edges"], amt["axioms"])
        if ok:
            print("\nOK   Consistency check passed.")
        else:
            print(f"\nFAIL {len(violations)} consistency violation(s):")
            for v in violations:
                print(f"  - {v}")

    if reason:
        reasoned = do_reasoning(amt["edges"], amt["axioms"])
        inferred = [e for e in reasoned if e.get("inferred")]
        print(f"\n     reasoning produced {len(inferred)} inferred edge(s)")

    if export_ttl_:
        ttl = export_ttl(
            amt["nodes"], amt["edges"], amt["concepts"], amt["roles"],
            amt["axioms"], rdf_graph=amt["graph"], prefix=amt["prefix"],
            with_reasoning=reason,
        )
        suffix = ".reasoned.ttl" if reason else ".ttl"
        path = out_dir / f"{stem}{suffix}"
        path.write_text(ttl, encoding="utf-8")
        print(f"OK   wrote {path}")

    if export_cypher_:
        cy = export_cypher(
            amt["nodes"], amt["edges"], amt["axioms"],
            with_reasoning=reason,
        )
        path = out_dir / f"{stem}.cypher"
        path.write_text(cy, encoding="utf-8")
        print(f"OK   wrote {path}")

    if export_csv_:
        nodes_p, edges_p = export_csv(
            amt["nodes"], amt["edges"], amt["axioms"],
            out_dir, with_reasoning=reason, prefix=stem,
        )
        print(f"OK   wrote {nodes_p}")
        print(f"OK   wrote {edges_p}")

    if export_html_:
        path = out_dir / f"{stem}.html"
        render_to_html(
            amt["nodes"], amt["edges"], amt["concepts"],
            output_path=path,
            reasoning=reason,
            axioms=amt["axioms"],
            height=height,
        )
        print(f"OK   wrote {path}")

    return amt


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(
        prog="amt-runner",
        description="Run the full AMT pipeline on one input file.",
    )
    p.add_argument("input", type=Path, help="AMT-compatible Turtle (.ttl) file")
    p.add_argument("-o", "--output-dir", type=Path, default=None,
                   help="Output directory (default: <input-dir>/out)")
    p.add_argument("--no-validate", action="store_true", help="Skip SHACL validation")
    p.add_argument("--no-reason",   action="store_true", help="Skip reasoning step")
    p.add_argument("--no-check",    action="store_true", help="Skip consistency check")
    p.add_argument("--no-info",     action="store_true", help="Skip ontology summary printout")
    p.add_argument("--ontology",    type=Path, default=None, help="Custom ontology folder")
    p.add_argument("--height", default="600px",
                   help="Canvas height for the HTML graph (default: 600px)")
    args = p.parse_args(argv)

    try:
        run_all(
            args.input,
            output_dir=args.output_dir,
            validate=not args.no_validate,
            reason=not args.no_reason,
            check=not args.no_check,
            info=not args.no_info,
            height=args.height,
            ontology_dir=args.ontology,
        )
    except FileNotFoundError as e:
        print(f"FAIL  Input file not found: {e}", file=sys.stderr)
        return 2
    except AMTValidationError:
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
