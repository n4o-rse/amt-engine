"""
Command-line interface for the Academic Meta Tool.

Usage examples
--------------
::

    amt input.ttl --info
    amt input.ttl --validate
    amt input.ttl --reason --export-ttl out.ttl
    amt input.ttl --reason --export-cypher out.cypher --export-html graph.html
    amt input.ttl --reason --export-csv out/
    amt input.ttl --reason --minimal --export-ttl out.ttl
    amt input.ttl --check
    amt input.ttl --validate-only

By default, ``--reason`` and ``--check`` validate the input first. Use
``--no-validate`` to disable.
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

from .diagnostics import diagnose, summarise
from .validation import format_violations
from . import (
    AMTValidationError,
    __version__,
    check_consistency,
    reason_with_stats,
    export_cypher,
    export_csv,
    export_ttl,
    load_amt,
    local_name,
    render_to_html,
    validate_against_shapes,
)


def _print_summary(amt: dict) -> None:
    print(
        f"OK  {len(amt['concepts'])} Concepts | "
        f"{len(amt['roles'])} Roles | "
        f"{len(amt['nodes'])} Nodes | "
        f"{len(amt['edges'])} Edges | "
        f"{len(amt['axioms'])} Axioms"
    )


def _print_info(amt: dict) -> None:
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
                details[k] = local_name(v) if isinstance(v, str) and v.startswith("http") else v
        print(f"  - {a['type']:20s}  {details}")


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="amt",
        description="Academic Meta Tool - Python edition",
    )
    p.add_argument("input", type=Path, help="AMT-compatible Turtle (.ttl) file")

    # Validation
    p.add_argument("--validate", action="store_true",
                   help="Run SHACL validation on the input file")
    p.add_argument("--no-validate", action="store_true",
                   help="Skip SHACL validation (default: validate before --reason/--check)")
    p.add_argument("--validate-only", action="store_true",
                   help="Only validate; do not parse/reason/export")

    # Pipeline steps
    p.add_argument("--reason", action="store_true",
                   help="Apply RoleChain, Inverse and Subsumption axioms before export")
    p.add_argument("--minimal", action="store_true",
                   help="With --reason: use SubsumptionAxioms to suppress inferred "
                        "edges that a finer edge already implies, instead of "
                        "spelling the role hierarchy out (no effect without "
                        "SubsumptionAxioms)")
    p.add_argument("--check", action="store_true",
                   help="Run consistency check")
    p.add_argument("--info", action="store_true",
                   help="Print ontology summary")

    # Outputs
    p.add_argument("--export-ttl", type=Path, metavar="PATH",
                   help="Write Turtle output to PATH")
    p.add_argument("--export-cypher", type=Path, metavar="PATH",
                   help="Write Neo4J Cypher output to PATH")
    p.add_argument("--export-csv", type=Path, metavar="DIR",
                   help="Write nodes.csv and edges.csv into DIR")
    p.add_argument("--export-html", type=Path, metavar="PATH",
                   help="Write standalone interactive HTML graph to PATH")
    p.add_argument("--no-vocabulary", action="store_true",
                   help="Skip AMT vocabulary scaffolding in TTL output")
    p.add_argument("--height", default="600px",
                   help="Canvas height for the HTML graph (default: 600px)")

    # Other
    p.add_argument("--ontology", type=Path, default=None,
                   help="Custom ontology folder (default: bundled ontology/)")
    p.add_argument("--version", action="version", version=f"%(prog)s {__version__}")
    return p


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)

    if not args.input.exists():
        print(f"FAIL  Input file not found: {args.input}", file=sys.stderr)
        return 2

    # ── Validation flow ────────────────────────────────────────────────
    # Validate by default if --reason or --check is requested. Always
    # validate if --validate / --validate-only is set. Never validate if
    # --no-validate is set.
    should_validate = (
        args.validate
        or args.validate_only
        or (
            (args.reason or args.check)
            and not args.no_validate
        )
    )

    if should_validate:
        print(f"VAL Validating {args.input.name} ...")
        ont_dir = args.ontology
        try:
            result = validate_against_shapes(args.input, ontology_dir=ont_dir)
        except FileNotFoundError as e:
            print(f"FAIL  {e}", file=sys.stderr)
            return 2
        if result.conforms:
            print("OK  Validation passed.")
        else:
            print(f"FAIL  Validation failed with {len(result.violations)} violation(s):")
            print(format_violations(result.violations))
            if args.validate_only or not args.no_validate:
                return 1

    if args.validate_only:
        return 0

    # ── Load ───────────────────────────────────────────────────────────
    print(f"LOAD Loading {args.input.name} ...")
    amt = load_amt(args.input, ontology_path=(args.ontology / "amt.ttl") if args.ontology else None)
    _print_summary(amt)

    findings = diagnose(amt)
    if findings:
        print(f"\nDIAG {summarise(findings)}:")
        for f in findings:
            print(f.format())

    if args.info:
        _print_info(amt)

    if args.minimal and not args.reason:
        print("WARN --minimal has no effect without --reason.", file=sys.stderr)

    # Reason once and reuse the result for the consistency check and for
    # every exporter, so a file with hundreds of role-chain axioms is not
    # run to a fixed point six times over.
    reasoned = None
    stats: dict = {}
    if args.reason or args.check:
        reasoned, stats = reason_with_stats(
            amt["edges"], amt["axioms"], minimal=args.minimal
        )

    if args.check:
        ok, violations = check_consistency(
            amt["edges"], amt["axioms"], reasoned=reasoned
        )
        if ok:
            print("\nOK  Consistency check passed.")
        else:
            print(f"\nFAIL  {len(violations)} consistency violation(s):")
            for v in violations:
                print(f"  - {v}")

    if args.reason:
        inferred = [e for e in reasoned if e.get("inferred")]
        print(f"  -> reasoning produced {len(inferred)} inferred edge(s)")
        if args.minimal:
            print(f"  -> minimal mode suppressed "
                  f"{stats.get('suppressed', 0)} redundant edge(s)")
        if not stats.get("reached_fixpoint", True):
            print("WARN reasoning hit the iteration limit; "
                  "the result may be incomplete.", file=sys.stderr)

    if args.export_ttl:
        ttl = export_ttl(
            amt["nodes"], amt["edges"], amt["concepts"], amt["roles"],
            amt["axioms"], rdf_graph=amt["graph"], prefix=amt["prefix"],
            with_reasoning=args.reason,
            include_vocabulary=not args.no_vocabulary,
            reasoned_edges=reasoned,
        )
        args.export_ttl.write_text(ttl, encoding="utf-8")
        print(f"OK  wrote {args.export_ttl}")

    if args.export_cypher:
        cy = export_cypher(
            amt["nodes"], amt["edges"], amt["axioms"],
            with_reasoning=args.reason, reasoned_edges=reasoned,
        )
        args.export_cypher.write_text(cy, encoding="utf-8")
        print(f"OK  wrote {args.export_cypher}")

    if args.export_csv:
        nodes_p, edges_p = export_csv(
            amt["nodes"], amt["edges"], amt["axioms"],
            args.export_csv, with_reasoning=args.reason,
            reasoned_edges=reasoned,
        )
        print(f"OK  wrote {nodes_p}")
        print(f"OK  wrote {edges_p}")

    if args.export_html:
        render_to_html(
            amt["nodes"], amt["edges"], amt["concepts"],
            output_path=args.export_html,
            reasoning=args.reason,
            axioms=amt["axioms"],
            height=args.height,
            reasoned_edges=reasoned,
        )
        print(f"OK  wrote {args.export_html}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
