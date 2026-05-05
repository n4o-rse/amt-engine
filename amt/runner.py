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
* write a Markdown run-report into the output folder

Usable as a library function (``run_all``) or as
``python -m amt.runner input.ttl``.

Output files are placed next to the input by default, under ``out/`` and
named after the input stem::

    examples/Potter.ttl
        -> out/Potter.reasoned.ttl
        -> out/Potter.cypher
        -> out/Potter.nodes.csv
        -> out/Potter.edges.csv
        -> out/Potter.html
        -> out/Potter.report.md
"""
from __future__ import annotations

import argparse
import sys
from datetime import datetime
from pathlib import Path

from . import (
    AMTValidationError,
    __version__,
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


# ─────────────────────────────────────────────────────────────────────────
# Run report
# ─────────────────────────────────────────────────────────────────────────
class RunReport:
    """Collects events across a pipeline run and renders them as Markdown.

    The report mirrors what the user sees on the terminal but with more
    detail (full IRIs, exact weights, every inferred edge). Designed to be
    skim-able later when looking at an old output folder and trying to
    reconstruct what produced it.
    """

    def __init__(self, input_path: Path, options: dict):
        self.started = datetime.now()
        self.finished: datetime | None = None
        self.input_path = input_path
        self.options = options
        self.summary: dict = {}
        self.validation: dict | None = None
        self.consistency: dict | None = None
        self.reasoning: dict | None = None
        self.outputs: list[Path] = []
        self.ontology_summary: dict | None = None

    def record_summary(self, amt: dict) -> None:
        self.summary = {
            "concepts": len(amt["concepts"]),
            "roles":    len(amt["roles"]),
            "nodes":    len(amt["nodes"]),
            "edges":    len(amt["edges"]),
            "axioms":   len(amt["axioms"]),
            "prefix":   amt.get("prefix", ""),
        }

    def record_ontology(self, amt: dict) -> None:
        self.ontology_summary = {
            "concepts": [
                {"iri": c["iri"], "label": c["label"]}
                for c in amt["concepts"].values()
            ],
            "roles": [
                {"iri": r["iri"], "label": r["label"],
                 "domain": r["domain"], "range": r["range"]}
                for r in amt["roles"].values()
            ],
            "axioms": [self._axiom_dict(a) for a in amt["axioms"]],
        }

    def record_validation(self, conforms: bool, violations: list) -> None:
        self.validation = {"conforms": conforms, "violations": list(violations)}

    def record_consistency(self, ok: bool, violations: list[str]) -> None:
        self.consistency = {"ok": ok, "violations": list(violations)}

    def record_reasoning(self, asserted_count: int,
                         inferred_edges: list[dict]) -> None:
        self.reasoning = {
            "asserted_count": asserted_count,
            "inferred":       list(inferred_edges),
        }

    def record_output(self, path: Path) -> None:
        self.outputs.append(Path(path))

    @staticmethod
    def _axiom_dict(a: dict) -> dict:
        out = {"type": a["type"], "iri": a.get("iri", "")}
        for k, v in a.items():
            if k in ("type", "iri"):
                continue
            if isinstance(v, list):
                out[k] = list(v)
            else:
                out[k] = v
        return out

    @staticmethod
    def _short(iri: str) -> str:
        if not isinstance(iri, str) or not iri:
            return str(iri)
        return iri.split("/")[-1].split("#")[-1] or iri

    def render(self) -> str:
        lines: list[str] = []

        lines.append(f"# AMT run report — `{self.input_path.name}`")
        lines.append("")
        lines.append(f"- **Started:**  `{self.started.isoformat(timespec='seconds')}`")
        if self.finished:
            lines.append(f"- **Finished:** `{self.finished.isoformat(timespec='seconds')}`")
            duration = (self.finished - self.started).total_seconds()
            lines.append(f"- **Duration:** {duration:.2f}s")
        lines.append(f"- **AMT version:** `{__version__}`")
        lines.append(f"- **Input file:**  `{self.input_path}`")
        lines.append("")

        # ── Options ─────────────────────────────────────────────────────
        lines.append("## Options")
        lines.append("")
        for key in ("validate", "reason", "check", "info",
                    "export_ttl", "export_cypher", "export_csv",
                    "export_html", "ontology_dir", "output_dir", "height"):
            if key in self.options:
                v = self.options[key]
                lines.append(f"- `{key}`: `{v}`")
        lines.append("")

        # ── Validation ──────────────────────────────────────────────────
        if self.validation is not None:
            lines.append("## SHACL validation")
            lines.append("")
            if self.validation["conforms"]:
                lines.append("✓ Validation passed — no violations.")
            else:
                vios = self.validation["violations"]
                lines.append(f"✗ Validation **failed** with {len(vios)} violation(s):")
                lines.append("")
                for i, v in enumerate(vios, 1):
                    msg = v.get("message", "?") if isinstance(v, dict) else str(v)
                    lines.append(f"{i}. {msg}")
            lines.append("")

        # ── Counts ──────────────────────────────────────────────────────
        if self.summary:
            lines.append("## Loaded")
            lines.append("")
            lines.append("| Concepts | Roles | Nodes | Edges | Axioms |")
            lines.append("|---:|---:|---:|---:|---:|")
            lines.append(
                f"| {self.summary['concepts']} | {self.summary['roles']} | "
                f"{self.summary['nodes']} | {self.summary['edges']} | "
                f"{self.summary['axioms']} |"
            )
            if self.summary.get("prefix"):
                lines.append("")
                lines.append(f"**Detected `ex:` prefix:** `{self.summary['prefix']}`")
            lines.append("")

        # ── Ontology summary ────────────────────────────────────────────
        if self.ontology_summary:
            lines.append("## Ontology contents")
            lines.append("")
            lines.append("### Concepts")
            lines.append("")
            for c in self.ontology_summary["concepts"]:
                lines.append(f"- `{self._short(c['iri'])}` — {c['label']}")
            lines.append("")
            lines.append("### Roles")
            lines.append("")
            lines.append("| Role | Domain → Range |")
            lines.append("|------|----------------|")
            for r in self.ontology_summary["roles"]:
                d = self._short(r["domain"])
                rg = self._short(r["range"])
                lines.append(f"| `{self._short(r['iri'])}` | {d} → {rg} |")
            lines.append("")
            lines.append("### Axioms")
            lines.append("")
            for ax in self.ontology_summary["axioms"]:
                lines.append(f"#### `{self._short(ax.get('iri', ''))}` ({ax['type']})")
                lines.append("")
                for k, v in ax.items():
                    if k in ("type", "iri"):
                        continue
                    if isinstance(v, list):
                        rendered = " ∘ ".join(self._short(x) for x in v)
                        lines.append(f"- **{k}:** {rendered}")
                    elif isinstance(v, str) and v.startswith("http"):
                        lines.append(f"- **{k}:** `{self._short(v)}`")
                    else:
                        lines.append(f"- **{k}:** `{v}`")
                lines.append("")

        # ── Consistency ─────────────────────────────────────────────────
        if self.consistency is not None:
            lines.append("## Consistency check")
            lines.append("")
            if self.consistency["ok"]:
                lines.append("✓ All integrity axioms satisfied.")
            else:
                vios = self.consistency["violations"]
                lines.append(f"✗ Found **{len(vios)}** integrity violation(s):")
                lines.append("")
                for i, v in enumerate(vios, 1):
                    lines.append(f"{i}. {v}")
            lines.append("")

        # ── Reasoning ───────────────────────────────────────────────────
        if self.reasoning is not None:
            lines.append("## Reasoning")
            lines.append("")
            inf = self.reasoning["inferred"]
            asserted = self.reasoning["asserted_count"]
            lines.append(
                f"Started from **{asserted}** asserted edges. "
                f"Reasoning produced **{len(inf)}** inferred edge(s)."
            )
            lines.append("")
            if inf:
                lines.append("| Source | Role | Target | Weight | Provenance |")
                lines.append("|--------|------|--------|-------:|------------|")
                for e in inf:
                    src = self._short(e["from"])
                    tgt = self._short(e["to"])
                    role = self._short(e["role"])
                    w = float(e["weight"])
                    prov = ", ".join(
                        f"`{self._short(p)}`" for p in (e.get("provenance") or [])
                    ) or "—"
                    lines.append(f"| {src} | `{role}` | {tgt} | {w:.6f} | {prov} |")
                lines.append("")

        # ── Outputs ─────────────────────────────────────────────────────
        if self.outputs:
            lines.append("## Output files")
            lines.append("")
            for p in self.outputs:
                size = p.stat().st_size if p.exists() else 0
                lines.append(f"- `{p.name}` — {size:,} bytes")
            lines.append("")

        lines.append("---")
        lines.append("")
        lines.append(f"*Generated by AMT runner v{__version__}.*")
        lines.append("")
        return "\n".join(lines)


def _write_report_safely(report: "RunReport", out_dir: Path, stem: str) -> Path | None:
    """Render and write the run report. Returns the path on success."""
    report.finished = datetime.now()
    try:
        text = report.render()
        path = out_dir / f"{stem}.report.md"
        path.write_text(text, encoding="utf-8")
        return path
    except Exception as e:
        # Reporting must never break the pipeline.
        print(f"WARN Could not write run report: {e}", file=sys.stderr)
        return None


# ─────────────────────────────────────────────────────────────────────────
# Pipeline
# ─────────────────────────────────────────────────────────────────────────
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
    write_report: bool = True,
    height: str = "600px",
    ontology_dir: str | Path | None = None,
) -> dict:
    """
    Run the full AMT pipeline. Returns the loaded ``amt`` dict so callers
    (notebook, tests) can keep working with it.

    A Markdown run-report is written into the output folder by default
    (``<stem>.report.md``); pass ``write_report=False`` to skip it.
    """
    input_path = Path(input_path)
    if not input_path.exists():
        raise FileNotFoundError(input_path)

    out_dir = Path(output_dir) if output_dir else input_path.parent / "out"
    if out_dir.exists():
        import shutil
        for entry in out_dir.iterdir():
            if entry.is_dir():
                shutil.rmtree(entry)
            else:
                entry.unlink()
    out_dir.mkdir(parents=True, exist_ok=True)
    stem = input_path.stem

    report = RunReport(input_path=input_path, options={
        "validate":      validate,
        "reason":        reason,
        "check":         check,
        "info":          info,
        "export_ttl":    export_ttl_,
        "export_cypher": export_cypher_,
        "export_csv":    export_csv_,
        "export_html":   export_html_,
        "ontology_dir":  str(ontology_dir) if ontology_dir else None,
        "output_dir":    str(out_dir),
        "height":        height,
    })

    if validate:
        print(f"VAL  Validating {input_path.name} ...")
        result = validate_against_shapes(input_path, ontology_dir=ontology_dir)
        report.record_validation(result.conforms, result.violations)
        if not result.conforms:
            print(f"FAIL Validation failed with {len(result.violations)} violation(s):")
            for i, v in enumerate(result.violations, 1):
                print(f"  [{i}] {v.get('message', '?')}")
            if write_report:
                _write_report_safely(report, out_dir, stem)
            raise AMTValidationError(result.report_text, result.violations)
        print("OK   Validation passed.")

    print(f"LOAD Loading {input_path} ...")
    ont_path = (Path(ontology_dir) / "amt.ttl") if ontology_dir else None
    amt = load_amt(input_path, ontology_path=ont_path)
    report.record_summary(amt)
    print(
        f"OK   {len(amt['concepts'])} Concepts | "
        f"{len(amt['roles'])} Roles | "
        f"{len(amt['nodes'])} Nodes | "
        f"{len(amt['edges'])} Edges | "
        f"{len(amt['axioms'])} Axioms"
    )

    if info:
        report.record_ontology(amt)
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
        report.record_consistency(ok, violations)
        if ok:
            print("\nOK   Consistency check passed.")
        else:
            print(f"\nFAIL {len(violations)} consistency violation(s):")
            for v in violations:
                print(f"  - {v}")

    if reason:
        reasoned = do_reasoning(amt["edges"], amt["axioms"])
        inferred = [e for e in reasoned if e.get("inferred")]
        report.record_reasoning(asserted_count=len(amt["edges"]),
                                inferred_edges=inferred)
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
        report.record_output(path)
        print(f"OK   wrote {path}")

    if export_cypher_:
        cy = export_cypher(
            amt["nodes"], amt["edges"], amt["axioms"],
            with_reasoning=reason,
        )
        path = out_dir / f"{stem}.cypher"
        path.write_text(cy, encoding="utf-8")
        report.record_output(path)
        print(f"OK   wrote {path}")

    if export_csv_:
        nodes_p, edges_p = export_csv(
            amt["nodes"], amt["edges"], amt["axioms"],
            out_dir, with_reasoning=reason, prefix=stem,
        )
        report.record_output(nodes_p)
        report.record_output(edges_p)
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
        report.record_output(path)
        print(f"OK   wrote {path}")

    if write_report:
        report_path = _write_report_safely(report, out_dir, stem)
        if report_path:
            print(f"OK   wrote {report_path}")

    return amt


# ─────────────────────────────────────────────────────────────────────────
# CLI entry point
# ─────────────────────────────────────────────────────────────────────────
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
    p.add_argument("--no-report",   action="store_true",
                   help="Skip writing the Markdown run report")
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
            write_report=not args.no_report,
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
