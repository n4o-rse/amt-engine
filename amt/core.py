"""
AMT Core — Data Model and Parser
================================

Pure parser. No reasoning, no validation, no export logic. Reads a Turtle
file (and, optionally, the AMT ontology for RDFS inference) and returns a
plain ``dict`` of the form documented in :func:`load_amt`.

The dict survives JSON serialisation modulo the embedded ``rdflib.Graph``
under the ``graph`` key, which is kept around for downstream tools that
want to issue SPARQL queries.

Edge schema
-----------

Every edge is a dict with these keys::

    {
        "role":       str,    # IRI of the role
        "from":       str,    # IRI of the source node (NB: SPARQL-style key)
        "to":         str,    # IRI of the target node
        "weight":     float,  # in [0, 1]
        "inferred":   bool,   # False for asserted, True for derived
        "provenance": list,   # IRIs of axioms that produced this edge
        "type":       str | None,   # fw:hasType IRI; None = default (vagueness)
        "method":     str | None,   # fw:hasMethod IRI
        "evidence":   list | None,  # fw:derivedFrom nodes, passed through
    }

``type``, ``method`` and ``evidence`` are the two optional columns of the
hextuple plus the evidence behind a statement (see :mod:`amt.fw`). All three
are ``None`` for a plain quadruple. The weight is read from ``amt:weight`` or
from ``fw:hasDegreeOfConnection``; if a statement carries both with different
values, ``amt:weight`` wins (and :func:`amt.diagnostics.diagnose` says so).
An evidence entry is ``{"id": IRI or None, "properties": [[predicate, n3], ...]}``
with the objects already written as Turtle terms; nested blank nodes are not
followed.

The ``"from"`` / ``"to"`` keys are kept (rather than ``"source"`` /
``"target"``) for round-trip compatibility with the original JS exporter
and the existing webviewer.
"""
from __future__ import annotations

from pathlib import Path
from typing import TypedDict

from rdflib import BNode, Graph, Namespace, RDF, RDFS, URIRef
from rdflib.collection import Collection

from ._resources import ontology_dir as _bundled_ontology_dir
from .fw import FW

# AMT vocabulary namespace
AMT = Namespace("http://academic-meta-tool.xyz/vocab#")
AMT_PFX = str(AMT)


# ─────────────────────────────────────────────────────────────────────────
# Type hints (lightweight – not enforced)
# ─────────────────────────────────────────────────────────────────────────
class Concept(TypedDict):
    iri: str
    label: str
    placeholder: str


class Role(TypedDict):
    iri: str
    label: str
    domain: str
    range: str


class Node(TypedDict):
    id: str
    label: str
    concept: str


# ─────────────────────────────────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────────────────────────────────
def local_name(iri: str) -> str:
    """Return the local name of an IRI (after the last ``#`` or ``/``)."""
    return str(iri).split("/")[-1].split("#")[-1]


_local = local_name  # private alias


def is_existing_path(text: str) -> bool:
    """
    True if ``text`` names an existing file. Turtle given as a string is not
    a path: a long one would make ``Path.exists`` raise "File name too long",
    so that error counts as "no".
    """
    try:
        return Path(text).exists()
    except (OSError, ValueError):
        return False


def _read_rdf_list(g: Graph, head) -> list[str]:
    """Return the IRIs of the items in an RDF list pointed at by ``head``."""
    if head is None:
        return []
    return [str(item) for item in Collection(g, head)]


def _normalise_axiom_entry(entry: dict, g: Graph) -> dict:
    """
    Post-process a freshly-parsed axiom dict.

    For RoleChainAxiom: collapse legacy ``antecedent1``/``antecedent2`` and
    modern ``antecedents`` (RDF list) into a single ``antecedents`` list of
    role IRIs. Both forms are accepted. The normalised list is what the
    reasoner consumes.

    For all axioms: convert the parsed ``logicParameter`` literal into a
    float when present.
    """
    if entry["type"] == "RoleChainAxiom":
        # Modern form: antecedents was already resolved into a list during
        # parsing. Legacy form: synthesise the list from antecedent1+2.
        if "antecedents" not in entry:
            if "antecedent1" in entry and "antecedent2" in entry:
                entry["antecedents"] = [entry["antecedent1"], entry["antecedent2"]]
            else:
                # SHACL would have caught this, but be defensive anyway.
                entry["antecedents"] = []

    if "logicParameter" in entry:
        try:
            entry["logicParameter"] = float(entry["logicParameter"])
        except (TypeError, ValueError):
            pass  # leave as-is; SHACL should have caught this

    return entry


def _first_iri(g: Graph, subject, predicate) -> str | None:
    """The smallest IRI object of ``predicate`` (sorted, so runs agree), or None."""
    values = sorted(str(o) for o in g.objects(subject, predicate) if isinstance(o, URIRef))
    return values[0] if values else None


def _read_evidence(g: Graph, stmt) -> list | None:
    """
    The ``fw:derivedFrom`` nodes of a statement, ready to be written again.

    Each node becomes ``{"id": IRI or None, "properties": [[p, n3], ...]}``.
    The properties are the node's own triples (for example ``rdf:type
    fw:TextEvidence`` and ``fw:sourceString "..."``), sorted; objects that are
    blank nodes are left out. Returns None if the statement has no evidence.
    """
    nodes = sorted(set(g.objects(stmt, FW.derivedFrom)), key=lambda n: (isinstance(n, URIRef) is False, str(n)))
    if not nodes:
        return None
    out = []
    for node in nodes:
        props = sorted(
            [str(p), o.n3()]
            for p, o in g.predicate_objects(node)
            if not isinstance(o, BNode)
        )
        out.append({"id": str(node) if isinstance(node, URIRef) else None, "properties": props})
    return out


# ─────────────────────────────────────────────────────────────────────────
# Loader
# ─────────────────────────────────────────────────────────────────────────
def load_amt(
    ttl_source: str | Path,
    *,
    ontology_path: str | Path | None = None,
    validate: bool = False,
) -> dict:
    """
    Parse a Turtle source and extract all AMT components.

    Parameters
    ----------
    ttl_source
        Path to a ``.ttl`` file, or a raw Turtle string.
    ontology_path
        Optional path to ``amt.ttl``. If given, the ontology is merged into
        the working graph so axiom-class detection works on data-only files
        that don't re-declare the AMT vocabulary. Defaults to the bundled
        ``ontology/amt.ttl`` if it exists.
    validate
        If True, run SHACL validation against the bundled
        ``ontology/amt-shapes.ttl`` before parsing. Raises
        :class:`amt.validation.AMTValidationError` on failure.

    Returns
    -------
    dict
        Keys: ``concepts``, ``roles``, ``nodes``, ``edges``, ``axioms``,
        ``graph`` (the data graph as an :class:`rdflib.Graph`),
        ``prefix`` (best-guess instance prefix, used by exporters).
    """
    if validate:
        # Local import to avoid pulling pyshacl into the import graph
        # of users who don't need validation.
        from .validation import validate_against_shapes, AMTValidationError
        result = validate_against_shapes(ttl_source)
        if not result.conforms:
            raise AMTValidationError(result.report_text, result.violations)

    g = Graph()
    src = str(ttl_source)
    if is_existing_path(src):
        g.parse(src, format="turtle")
    else:
        g.parse(data=src, format="turtle")

    # Optionally merge the ontology so axiom detection works on data-only
    # files. We use a SEPARATE graph for vocabulary lookups so the
    # downstream "amt-dict" (which represents the user's data) doesn't get
    # polluted with vocabulary triples.
    vocab = Graph()
    if ontology_path is None:
        bundled = _bundled_ontology_dir()
        if bundled is not None:
            ontology_path = bundled / "amt.ttl"
    if ontology_path is not None:
        vocab.parse(str(ontology_path), format="turtle")

    # Combined graph used only for vocabulary-aware queries below.
    lookup = g + vocab if len(vocab) else g

    # ── Concepts ────────────────────────────────────────────────────────
    concepts: dict[str, Concept] = {}
    for c in g.subjects(RDF.type, AMT.Concept):
        label = str(g.value(c, RDFS.label) or _local(c))
        placeholder = str(g.value(c, AMT.placeholder) or label)
        concepts[str(c)] = {"iri": str(c), "label": label, "placeholder": placeholder}

    # ── Roles ───────────────────────────────────────────────────────────
    roles: dict[str, Role] = {}
    for r in sorted(
        g.subjects(RDF.type, AMT.Role),
        key=lambda x: str(g.value(x, RDFS.label) or x),
    ):
        label = str(g.value(r, RDFS.label) or _local(r))
        domain = str(g.value(r, RDFS.domain) or "")
        range_ = str(g.value(r, RDFS.range) or "")
        roles[str(r)] = {
            "iri": str(r),
            "label": label,
            "domain": domain,
            "range": range_,
        }

    # ── Nodes (instances) ───────────────────────────────────────────────
    nodes: dict[str, Node] = {}
    for concept_iri in concepts:
        for inst in g.subjects(AMT.instanceOf, URIRef(concept_iri)):
            label = str(g.value(inst, RDFS.label) or _local(inst))
            nodes[str(inst)] = {
                "id": str(inst),
                "label": label,
                "concept": concept_iri,
            }

    # ── Edges (reified statements with weight) ──────────────────────────
    # The weight is amt:weight or, equivalently, fw:hasDegreeOfConnection.
    # amt:weight wins if a statement has both with different values.
    weighted = list(g.subjects(AMT.weight, None))
    known = set(weighted)
    weighted += sorted(
        {s for s in g.subjects(FW.hasDegreeOfConnection, None)} - known, key=str
    )
    edges: list[dict] = []
    for stmt in weighted:
        frm = g.value(stmt, RDF.subject)
        role = g.value(stmt, RDF.predicate)
        to = g.value(stmt, RDF.object)
        w = g.value(stmt, AMT.weight)
        if w is None:
            w = g.value(stmt, FW.hasDegreeOfConnection)
        if frm and role and to and w is not None:
            edges.append(
                {
                    "role":       str(role),
                    "from":       str(frm),
                    "to":         str(to),
                    "weight":     min(float(w), 1.0),
                    "inferred":   False,
                    "provenance": [],
                    "type":       _first_iri(g, stmt, FW.hasType),
                    "method":     _first_iri(g, stmt, FW.hasMethod),
                    "evidence":   _read_evidence(g, stmt),
                }
            )

    # ── Axioms ──────────────────────────────────────────────────────────
    # Collect known axiom subclasses. Use the lookup graph (data + vocab)
    # so that data-only files still find the hierarchy in amt.ttl.
    axiom_types: set = set()
    for cls in lookup.subjects(RDFS.subClassOf, AMT.Axiom):
        axiom_types.add(cls)
        for sub in lookup.subjects(RDFS.subClassOf, cls):
            axiom_types.add(sub)
    # Defensive fallback if neither vocab nor data declared the hierarchy
    if not axiom_types:
        axiom_types = {
            AMT.RoleChainAxiom, AMT.InverseAxiom, AMT.SubsumptionAxiom,
            AMT.DisjointAxiom, AMT.SelfDisjointAxiom,
        }

    # Sort both loops. Iterating a set makes the order in which RoleChain,
    # Inverse and Subsumption axioms are applied depend on string hashing,
    # which changes the order of amt:provenance lists between runs and so
    # makes three of the six exported files non-byte-identical. Sorting by
    # IRI pins the order across processes, machines and Python versions.
    axioms: list[dict] = []
    for atype in sorted(axiom_types, key=str):
        for axiom in sorted(g.subjects(RDF.type, atype), key=str):
            entry: dict = {"type": _local(atype), "iri": str(axiom)}
            for _, p, o in g.triples((axiom, None, None)):
                if p == RDF.type:
                    continue
                key = _local(p)
                # For amt:antecedents we resolve the RDF list inline,
                # because once we stringify the list head BNode we lose the
                # ability to dereference it.
                if p == AMT.antecedents:
                    entry["antecedents"] = _read_rdf_list(g, o)
                else:
                    entry[key] = str(o)
            axioms.append(_normalise_axiom_entry(entry, g))

    # ── Best-guess prefix (used by exporters for short ``ex:`` names) ───
    # Pick the most common prefix among Concepts, Roles, Nodes and Axioms.
    # This is more robust than just looking at the first node, especially
    # for SKOS-style mappings where instances span multiple vocabularies
    # (e.g. AAT, Wikidata, project-internal).
    prefix = ""
    iri_pool: list[str] = []
    iri_pool += [c["iri"] for c in concepts.values()]
    iri_pool += [r["iri"] for r in roles.values()]
    iri_pool += [n["id"] for n in nodes.values()]
    iri_pool += [a["iri"] for a in axioms if a.get("iri", "").startswith("http")]
    if iri_pool:
        from collections import Counter
        prefixes = [iri.rsplit("/", 1)[0] + "/" for iri in iri_pool]
        # Exclude well-known vocabularies — they should never become "ex:"
        prefixes = [
            p for p in prefixes
            if not p.startswith(AMT_PFX)
            and not p.startswith("http://www.w3.org/")
            and not p.startswith("http://purl.org/")
        ]
        if prefixes:
            prefix = Counter(prefixes).most_common(1)[0][0]

    return {
        "concepts": concepts,
        "roles":    roles,
        "nodes":    nodes,
        "edges":    edges,
        "axioms":   axioms,
        "graph":    g,
        "prefix":   prefix,
    }
