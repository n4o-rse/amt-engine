"""
AMT Exporters
=============

* :func:`export_ttl`    – Turtle, round-trip-compatible with :func:`amt.core.load_amt`.
                          Inferred edges carry ``amt:inferred "true"`` and
                          ``amt:provenance`` references to the originating axioms.
  Weights are written as ``xsd:decimal``. ``fw:hasType``, ``fw:hasMethod``
                          and ``fw:derivedFrom`` appear only on edges that
                          have them; the default type (vagueness) is never
                          written on an edge that does not already carry it.
* :func:`export_cypher` – Neo4J Cypher, with the same provenance semantics
                          encoded as relationship properties.
* :func:`export_csv`    – Two CSV files (``nodes.csv`` and ``edges.csv``),
                          suitable for import into Pandas, Excel, or any
                          downstream tabular pipeline.

All three accept ``with_reasoning=True`` to include inferred edges. TTL has
an additional ``include_vocabulary=True`` (default) flag that controls
whether the AMT vocabulary scaffolding is emitted alongside the data.
"""
from __future__ import annotations

import csv
import re
from pathlib import Path

from rdflib import Graph

from .core import local_name
from .fw import FW_PFX, effective_type
from .reasoning import do_reasoning


def _resolve_display_edges(
    edges: list,
    axioms: list,
    with_reasoning: bool,
    reasoned_edges: list | None,
) -> list:
    """
    Decide which edge list an exporter should write.

    Without ``with_reasoning`` the asserted edges are written as they are.
    With it, a caller-supplied ``reasoned_edges`` wins over reasoning again
    here — that is how ``minimal=True`` and other non-default reasoning
    options reach the exporters, and it saves a redundant fixed point when
    several formats are written from one run.
    """
    if not with_reasoning:
        return edges
    if reasoned_edges is not None:
        return reasoned_edges
    return do_reasoning(edges, axioms)


# ─────────────────────────────────────────────────────────────────────────
# TTL export
# ─────────────────────────────────────────────────────────────────────────
def export_ttl(
    nodes: dict,
    edges: list,
    concepts: dict,
    roles: dict,
    axioms: list,
    rdf_graph: Graph,            # kept for API parity / future use
    prefix: str,
    *,
    with_reasoning: bool = False,
    include_vocabulary: bool = True,
    reasoned_edges: list | None = None,
) -> str:
    """
    Serialise the current AMT state to Turtle.

    Parameters
    ----------
    with_reasoning
        Include inferred edges in the output.
    reasoned_edges
        An already-reasoned edge list. Pass it to avoid running the fixed
        point again, and to export a graph produced with non-default
        reasoning options such as ``minimal=True``. Ignored unless
        ``with_reasoning`` is set.
    include_vocabulary
        Emit AMT vocabulary scaffolding (subClassOf hierarchy, Logic
        instances) alongside the data. Default True for backward
        compatibility with the original JS exporter and the webviewer,
        which expect to find these triples in the data file. Set False to
        produce a cleaner data-only file that validates against a separate
        ontology.
    """
    AMT_NS  = "http://academic-meta-tool.xyz/vocab#"
    RDF_NS  = "http://www.w3.org/1999/02/22-rdf-syntax-ns#"
    RDFS_NS = "http://www.w3.org/2000/01/rdf-schema#"
    XSD_NS  = "http://www.w3.org/2001/XMLSchema#"

    # Well-known prefixes that we collapse if they appear in the data.
    # Order matters — longer matches first.
    KNOWN_PREFIXES = [
        ("skos:",     "http://www.w3.org/2004/02/skos/core#"),
        ("skosplus:", "http://w3id.org/skos-plus/"),
        ("wd:",       "http://www.wikidata.org/entity/"),
        ("aat:",      "http://vocab.getty.edu/aat/"),
        ("dct:",      "http://purl.org/dc/terms/"),
        ("foaf:",     "http://xmlns.com/foaf/0.1/"),
        ("fw:",       FW_PFX),
    ]
    # Detect which of the known prefixes actually appear in the data, so
    # we only declare what we use.
    used_known: list[tuple[str, str]] = []

    display_edges = _resolve_display_edges(edges, axioms, with_reasoning, reasoned_edges)
    asserted_edges = [e for e in display_edges if not e.get("inferred")]
    inferred_edges = [e for e in display_edges if e.get("inferred")]

    def pfx(iri: str) -> str:
        if not iri:
            return iri
        if prefix and iri.startswith(prefix):
            return "ex:" + iri[len(prefix):]
        if iri.startswith(AMT_NS):
            return "amt:" + iri[len(AMT_NS):]
        if iri.startswith(RDF_NS):
            return "rdf:" + iri[len(RDF_NS):]
        if iri.startswith(RDFS_NS):
            return "rdfs:" + iri[len(RDFS_NS):]
        if iri.startswith(XSD_NS):
            return "xsd:" + iri[len(XSD_NS):]
        for short, long in KNOWN_PREFIXES:
            if iri.startswith(long):
                if (short, long) not in used_known:
                    used_known.append((short, long))
                return short + iri[len(long):]
        return f"<{iri}>"

    def hextuple_parts(e: dict, width: int) -> tuple[list[str], list[str]]:
        """Property lines for type, method and evidence of one edge, plus the
        triples of evidence nodes that have an IRI (written once, after)."""
        parts: list[str] = []
        extra: list[str] = []
        if e.get("type"):
            parts.append(f'    {"fw:hasType":<{width}}{pfx(e["type"])}')
        if e.get("method"):
            parts.append(f'    {"fw:hasMethod":<{width}}{pfx(e["method"])}')
        for ev in e.get("evidence") or []:
            props = [
                f"{pfx(p_)} " + (pfx(o_[1:-1]) if o_.startswith("<") and o_.endswith(">") else o_)
                for p_, o_ in ev.get("properties", [])
            ]
            if ev.get("id"):
                parts.append(f'    {"fw:derivedFrom":<{width}}{pfx(ev["id"])}')
                if ev["id"] not in written_evidence:
                    written_evidence.add(ev["id"])
                    extra += [pfx(ev["id"])] + [
                        f"    {x} {';' if i < len(props) - 1 else '.'}" for i, x in enumerate(props)
                    ] + [""] if props else []
            else:
                parts.append(f'    {"fw:derivedFrom":<{width}}[ ' + " ; ".join(props) + " ]")
        return parts, extra

    written_evidence: set[str] = set()

    # Pre-scan all IRIs to collect used known prefixes BEFORE writing the
    # @prefix declarations. We build a small list of every IRI that will
    # appear in the output and run it through pfx() to populate used_known.
    _scan = []
    for c in concepts.values():
        _scan.append(c["iri"])
    for r in roles.values():
        _scan += [r["iri"], r["domain"], r["range"]]
    for n in nodes.values():
        _scan += [n["id"], n["concept"]]
    for a in axioms:
        for v in a.values():
            if isinstance(v, str) and v.startswith("http"):
                _scan.append(v)
            elif isinstance(v, list):
                _scan += [x for x in v if isinstance(x, str) and x.startswith("http")]
    for e in display_edges:
        _scan += [e["from"], e["to"], e["role"]]
        _scan += list(e.get("provenance") or [])
        _scan += [x for x in (e.get("type"), e.get("method")) if x]
        for ev in e.get("evidence") or []:
            if ev.get("id"):
                _scan.append(ev["id"])
            for p_, o_ in ev.get("properties", []):
                _scan.append(p_)
                if o_.startswith("<") and o_.endswith(">"):
                    _scan.append(o_[1:-1])
    for iri in _scan:
        pfx(iri)  # populates used_known as a side-effect
    # fw:hasType, fw:hasMethod and fw:derivedFrom are written by name, not
    # through pfx(), so declare the prefix whenever an edge carries one.
    if any(e.get("type") or e.get("method") or e.get("evidence") for e in display_edges):
        if ("fw:", FW_PFX) not in used_known:
            used_known.append(("fw:", FW_PFX))

    lines: list[str] = [
        f"@prefix amt:  <{AMT_NS}> .",
        f"@prefix rdf:  <{RDF_NS}> .",
        f"@prefix rdfs: <{RDFS_NS}> .",
        f"@prefix xsd:  <{XSD_NS}> .",
    ]
    for short, long in used_known:
        lines.append(f"@prefix {short:9s} <{long}> .")
    if prefix:
        lines.append(f"@prefix ex:   <{prefix}> .")
    lines.append("")

    # Concepts
    lines.append("# Concepts")
    for c in concepts.values():
        lines += [
            pfx(c["iri"]),
            "    rdf:type        amt:Concept ;",
            f'    rdfs:label      "{c["label"]}" ;',
            f'    amt:placeholder "{c["placeholder"]}" .',
            "",
        ]

    # Roles
    lines.append("# Roles")
    for r in roles.values():
        lines += [
            pfx(r["iri"]),
            "    rdf:type      amt:Role ;",
            f'    rdfs:label    "{r["label"]}" ;',
            f'    rdfs:domain   {pfx(r["domain"])} ;',
            f'    rdfs:range    {pfx(r["range"])} .',
            "",
        ]

    # Instances
    lines.append("# Instances")
    for n in nodes.values():
        lines += [
            pfx(n["id"]),
            f'    amt:instanceOf  {pfx(n["concept"])} ;',
            f'    rdfs:label      "{n["label"]}" .',
            "",
        ]

    # AMT vocabulary scaffolding (optional)
    if axioms and include_vocabulary:
        lines.append("# AMT vocabulary (needed for axiom recognition)")
        used_types = sorted({ax.get("type", "Axiom") for ax in axioms})
        lines.append("amt:Axiom rdfs:subClassOf rdfs:Class .")
        lines.append("amt:InferenceAxiom rdfs:subClassOf amt:Axiom .")
        lines.append("amt:IntegrityAxiom rdfs:subClassOf amt:Axiom .")
        _AXIOM_PARENT = {
            "RoleChainAxiom":    "InferenceAxiom",
            "InverseAxiom":      "InferenceAxiom",
            "DisjointAxiom":     "IntegrityAxiom",
            "SelfDisjointAxiom": "IntegrityAxiom",
        }
        for t in used_types:
            parent = _AXIOM_PARENT.get(t, "Axiom")
            lines.append(f"amt:{t} rdfs:subClassOf amt:{parent} .")
        lines.append("amt:Logic rdfs:subClassOf rdfs:Class .")
        for op in (
            "GoedelLogic", "ProductLogic", "LukasiewiczLogic",
            "EinsteinProduct", "GeometricMean", "HamacherProduct",
        ):
            lines.append(f"amt:{op} rdf:type amt:Logic .")
        lines.append("")

    # Axioms
    if axioms:
        lines.append("# Axioms")
        for idx, ax in enumerate(axioms, start=1):
            atype = ax.get("type", "Axiom")
            iri = ax.get("iri") or f"ex:AX{idx:04d}"
            iri_short = pfx(iri) if iri.startswith("http") else iri
            lines.append(f"{iri_short} rdf:type amt:{atype} .")
            for k, v in ax.items():
                if k in ("type", "iri"):
                    continue
                if k == "antecedents":
                    # Always emit the modern RDF-list form. Skip if the
                    # legacy antecedent1/2 fields are also present —
                    # they'll be emitted separately and SHACL forbids both
                    # at once.
                    if "antecedent1" in ax and "antecedent2" in ax:
                        continue
                    items = " ".join(pfx(role) for role in v)
                    lines.append(f"{iri_short} amt:antecedents ( {items} ) .")
                    continue
                if isinstance(v, str) and v.startswith("http"):
                    rendered = pfx(v)
                elif isinstance(v, (int, float)):
                    rendered = f'"{v}"^^xsd:decimal'
                else:
                    rendered = f'"{v}"'
                lines.append(f"{iri_short} amt:{k} {rendered} .")
            lines.append("")

    # Asserted assertions (reified statements)
    lines.append("# Original Assertions")
    pending: list[str] = []
    for j, e in enumerate(asserted_edges):
        w = min(float(e["weight"]), 1.0)
        bn = f"_:a{j+1}"
        parts, extra = hextuple_parts(e, 14)
        pending += extra
        lines += [
            bn,
            f'    rdf:subject   {pfx(e["from"])} ;',
            f'    rdf:predicate {pfx(e["role"])} ;',
            f'    rdf:object    {pfx(e["to"])} ;',
            f'    amt:weight    "{w:.6f}"^^xsd:decimal' + (" ;" if parts else " ."),
        ]
        for i, part in enumerate(parts):
            lines.append(part + (" ;" if i < len(parts) - 1 else " ."))
        lines.append("")

    # Inferred assertions, with provenance
    if with_reasoning and inferred_edges:
        lines.append("# Inferred Assertions")
        for k, e in enumerate(inferred_edges):
            w = min(float(e["weight"]), 1.0)
            bn = f"_:i{k+1}"
            block = [
                bn,
                f'    rdf:subject    {pfx(e["from"])} ;',
                f'    rdf:predicate  {pfx(e["role"])} ;',
                f'    rdf:object     {pfx(e["to"])} ;',
                f'    amt:weight     "{w:.6f}"^^xsd:decimal ;',
            ]
            parts, extra = hextuple_parts(e, 15)
            pending += extra
            block += [part + " ;" for part in parts]
            block.append('    amt:inferred   "true"^^xsd:boolean')
            prov = e.get("provenance") or []
            if prov:
                prov_part = ", ".join(pfx(p) for p in prov)
                block[-1] += " ;"
                block.append(f"    amt:provenance {prov_part} .")
            else:
                block[-1] += " ."
            block.append("")
            lines += block

    if pending:
        lines.append("# Evidence")
        lines += pending

    return "\n".join(lines)


# ─────────────────────────────────────────────────────────────────────────
# Cypher export
# ─────────────────────────────────────────────────────────────────────────
def export_cypher(
    nodes: dict,
    edges: list,
    axioms: list,
    *,
    with_reasoning: bool = False,
    reasoned_edges: list | None = None,
) -> str:
    """Serialise to Neo4J Cypher. Inferred edges carry inferred=true and
    a provenance list (semicolon-separated axiom local names).

    ``reasoned_edges`` works as in :func:`export_ttl`."""

    def cypher_safe(s: str) -> str:
        return re.sub(r"[^a-zA-Z0-9_]", "_", s)

    display_edges = _resolve_display_edges(edges, axioms, with_reasoning, reasoned_edges)
    inferred_count = sum(1 for e in display_edges if e.get("inferred"))

    var_map = {n["id"]: cypher_safe(local_name(n["id"])) for n in nodes.values()}

    lines = [
        "// AMT Cypher export",
        f"// Nodes: {len(nodes)}  Edges: {len(display_edges)}",
        f"// (inferred: {inferred_count})",
        "",
        "// Step 1: nodes",
    ]

    var_list = []
    node_lines = []
    for n in nodes.values():
        var = var_map[n["id"]]
        label = cypher_safe(local_name(n["concept"]))
        lbl = n["label"].replace('"', '\\"')
        node_lines.append(
            f'MERGE ({var}:{label} {{id: "{local_name(n["id"])}"}})\n'
            f'  ON CREATE SET {var}.label = "{lbl}", '
            f'{var}.concept = "{local_name(n["concept"])}"'
        )
        var_list.append(var)

    lines.append("\n".join(node_lines))
    if var_list:
        lines.append("WITH " + ", ".join(var_list))
    lines.append("")
    lines.append("// Step 2: relationships")

    for e in display_edges:
        w = round(min(float(e["weight"]), 1.0), 6)
        rel = cypher_safe(local_name(e["role"])).upper()
        fv = var_map.get(e["from"], cypher_safe(local_name(e["from"])))
        tv = var_map.get(e["to"], cypher_safe(local_name(e["to"])))
        inferred = "true" if e.get("inferred") else "false"
        prov_list = e.get("provenance") or []
        prov_str = ";".join(local_name(p) for p in prov_list)
        method = f', method: "{local_name(e["method"])}"' if e.get("method") else ""
        lines.append(
            f"MERGE ({fv})-[:{rel} {{weight: {w}, "
            f'role: "{local_name(e["role"])}", inferred: {inferred}, '
            f'provenance: "{prov_str}", '
            f'type: "{local_name(effective_type(e))}"{method}}}]->({tv})'
        )

    lines += ["", "RETURN *"]
    return "\n".join(lines)


# ─────────────────────────────────────────────────────────────────────────
# CSV export — two files
# ─────────────────────────────────────────────────────────────────────────
def export_csv(
    nodes: dict,
    edges: list,
    axioms: list,
    output_dir: str | Path,
    *,
    with_reasoning: bool = False,
    prefix: str = "",
    reasoned_edges: list | None = None,
) -> tuple[Path, Path]:
    """
    Write a nodes CSV and an edges CSV into ``output_dir``.

    Parameters
    ----------
    output_dir
        Directory the files are written into. Created if it doesn't exist.
    reasoned_edges
        An already-reasoned edge list; works as in :func:`export_ttl`.
    prefix
        Optional filename prefix. Without it the files are called
        ``nodes.csv`` and ``edges.csv``. With ``prefix="foo"`` they are
        called ``foo.nodes.csv`` and ``foo.edges.csv`` — useful when
        multiple datasets share an output directory.

    Schema:

    ``[prefix.]nodes.csv``  : ``iri, label, concept_iri``
    ``[prefix.]edges.csv``  : ``source_iri, target_iri, role_iri, weight, inferred, provenance, type, method``

    The ``provenance`` column is a semicolon-separated list of axiom IRIs
    (empty for asserted edges). ``type`` is the effective type IRI (an edge
    without an explicit type shows ``fw:Vagueness``); ``method`` is empty if
    the edge has none. The two columns come last, so readers that take the
    first six columns keep working.

    Returns the two file paths in (nodes, edges) order.
    """
    out_dir = Path(output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    display_edges = _resolve_display_edges(edges, axioms, with_reasoning, reasoned_edges)

    stem = f"{prefix}." if prefix else ""
    nodes_path = out_dir / f"{stem}nodes.csv"
    edges_path = out_dir / f"{stem}edges.csv"

    with nodes_path.open("w", encoding="utf-8", newline="") as f:
        w = csv.writer(f)
        w.writerow(["iri", "label", "concept_iri"])
        for n in nodes.values():
            w.writerow([n["id"], n["label"], n["concept"]])

    with edges_path.open("w", encoding="utf-8", newline="") as f:
        w = csv.writer(f)
        w.writerow([
            "source_iri", "target_iri", "role_iri",
            "weight", "inferred", "provenance", "type", "method",
        ])
        for e in display_edges:
            prov = ";".join(e.get("provenance") or [])
            w.writerow([
                e["from"], e["to"], e["role"],
                f"{float(e['weight']):.6f}",
                "true" if e.get("inferred") else "false",
                prov,
                effective_type(e),
                e.get("method") or "",
            ])

    return (nodes_path, edges_path)


# ─────────────────────────────────────────────────────────────────────────
# Convenience wrappers — write to disk in one call
# ─────────────────────────────────────────────────────────────────────────
def write_ttl(path: str | Path, *args, **kwargs) -> Path:
    """Convenience wrapper: :func:`export_ttl` + write to disk."""
    out = Path(path)
    out.write_text(export_ttl(*args, **kwargs), encoding="utf-8")
    return out


def write_cypher(path: str | Path, *args, **kwargs) -> Path:
    """Convenience wrapper: :func:`export_cypher` + write to disk."""
    out = Path(path)
    out.write_text(export_cypher(*args, **kwargs), encoding="utf-8")
    return out
