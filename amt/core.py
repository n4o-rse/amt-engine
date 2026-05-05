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
    }

The ``"from"`` / ``"to"`` keys are kept (rather than ``"source"`` /
``"target"``) for round-trip compatibility with the original JS exporter
and the existing webviewer.
"""
from __future__ import annotations

from pathlib import Path
from typing import TypedDict

from rdflib import Graph, Namespace, RDF, RDFS, URIRef
from rdflib.collection import Collection

# AMT vocabulary namespace
AMT = Namespace("http://academic-meta-tool.xyz/vocab#")
AMT_PFX = str(AMT)

# Where the bundled ontology lives by default. Resolved relative to this
# file so the package works whether installed via pip or run from a clone.
_DEFAULT_ONTOLOGY_DIR = Path(__file__).resolve().parent.parent / "ontology"


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
    if Path(src).exists():
        g.parse(src, format="turtle")
    else:
        g.parse(data=src, format="turtle")

    # Optionally merge the ontology so axiom detection works on data-only
    # files. We use a SEPARATE graph for vocabulary lookups so the
    # downstream "amt-dict" (which represents the user's data) doesn't get
    # polluted with vocabulary triples.
    vocab = Graph()
    if ontology_path is None and _DEFAULT_ONTOLOGY_DIR.exists():
        candidate = _DEFAULT_ONTOLOGY_DIR / "amt.ttl"
        if candidate.exists():
            ontology_path = candidate
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
    edges: list[dict] = []
    for stmt in g.subjects(AMT.weight, None):
        frm = g.value(stmt, RDF.subject)
        role = g.value(stmt, RDF.predicate)
        to = g.value(stmt, RDF.object)
        w = g.value(stmt, AMT.weight)
        if frm and role and to and w is not None:
            edges.append(
                {
                    "role":       str(role),
                    "from":       str(frm),
                    "to":         str(to),
                    "weight":     min(float(w), 1.0),
                    "inferred":   False,
                    "provenance": [],
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
            AMT.RoleChainAxiom, AMT.InverseAxiom,
            AMT.DisjointAxiom, AMT.SelfDisjointAxiom,
        }

    axioms: list[dict] = []
    for atype in axiom_types:
        for axiom in g.subjects(RDF.type, atype):
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
