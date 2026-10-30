"""
AMT Diagnostics
===============

Plain-language checks for mistakes that SHACL cannot see and that the loader
would otherwise swallow without a word.

The SHACL shapes (``ontology/amt-shapes.ttl``) say whether a file is *well
formed*. They do not say whether the file *does what its author meant*. The
typical case: an edge points at a node that was never declared as an instance
of a Concept. The reasoner then has an edge but no node to draw it to, the
exporters carry on, and the visualisation used to stop with an
``AssertionError`` from the drawing library. :func:`diagnose` finds such
cases up front and says which IRI is meant and what to add.

Every finding names the IRI it is about, so nobody has to search a file of
thousands of lines for "a concept without a label".

Usage::

    amt = load_amt("data.ttl")
    for f in diagnose(amt):
        print(f.format())

Findings have a level:

``error``
    The result will be incomplete or wrong (an edge cannot be drawn, a node
    is silently dropped).
``warning``
    Probably not what you meant, but the pipeline can continue.
``note``
    Information; nothing needs to be done.
"""
from __future__ import annotations

from dataclasses import dataclass, field

from rdflib import RDF, RDFS, Graph, URIRef

from .core import AMT, local_name
from .fw import FW, KNOWN_TYPES

LEVELS = ("error", "warning", "note")


@dataclass(frozen=True)
class Finding:
    """One diagnostic message about one IRI."""

    level: str          # "error" | "warning" | "note"
    code: str           # stable identifier, e.g. "AMT-E101"
    subject: str        # the IRI (or blank-node id) the finding is about
    message: str        # what is wrong, in one sentence
    hint: str = ""      # what to do about it
    related: tuple[str, ...] = field(default_factory=tuple)

    def format(self, *, indent: str = "  ") -> str:
        """Render as the text block the command line prints."""
        tag = {"error": "ERR ", "warning": "WARN", "note": "NOTE"}[self.level]
        lines = [f"{tag} [{self.code}] {self.message}"]
        if self.hint:
            for i, row in enumerate(self.hint.splitlines()):
                lines.append(f"{indent}{'->' if i == 0 else '  '} {row}")
        return "\n".join(lines)


def _angle(iri: str) -> str:
    return f"<{iri}>"


def _concept_example(concepts: dict) -> str:
    """A concept IRI to use in a hint: the first declared one, else a placeholder."""
    if concepts:
        return _angle(sorted(concepts)[0])
    return "<https://example.org/YourConcept>"


def _weighted_statements(g: Graph) -> list:
    """Every statement with a weight: amt:weight or fw:hasDegreeOfConnection."""
    found = set(g.subjects(AMT.weight, None)) | set(g.subjects(FW.hasDegreeOfConnection, None))
    return sorted(found, key=str)


def _triple_text(frm: str, role: str, to: str) -> str:
    return f"{local_name(frm)} {local_name(role)} {local_name(to)}"


def diagnose(amt: dict) -> list[Finding]:
    """
    Check a loaded AMT dict (the result of :func:`amt.core.load_amt`).

    The findings come back in a fixed order (errors first, then by code and
    IRI), so two runs on the same file print the same text.
    """
    g: Graph = amt["graph"]
    nodes: dict = amt["nodes"]
    concepts: dict = amt["concepts"]
    roles: dict = amt["roles"]
    edges: list = amt["edges"]
    out: list[Finding] = []

    # ── E101: edge ends that are not nodes (one finding for all of them) ─
    dangling: dict[str, set[str]] = {}
    for e in edges:
        for end, side in ((e["from"], "subject"), (e["to"], "object")):
            if end not in nodes:
                dangling.setdefault(end, set()).add(side)
    if dangling:
        iris = sorted(dangling)
        shown = iris[:8]
        lines = [f"{_angle(i)} amt:instanceOf {_concept_example(concepts)} ; rdfs:label \"...\" ." for i in shown]
        if len(iris) > len(shown):
            lines.append(f"# ... and {len(iris) - len(shown)} more")
        out.append(Finding(
            "error", "AMT-E101", iris[0],
            f"{len(iris)} IRI(s) are the subject or object of a weighted statement but are not AMT nodes: "
            + ", ".join(_angle(i) for i in shown[:3]) + (", ..." if len(iris) > 3 else ""),
            "Every end of an edge needs an amt:instanceOf, otherwise the reasoner cannot place it. Add, for each, e.g.:\n"
            + "\n".join(lines) + "\n"
            "(use a second Concept for them, such as an 'Authority' concept, if they are not of the same kind as the others)",
            related=tuple(iris),
        ))

    # ── E102: instanceOf points at something that is not a declared Concept ─
    undeclared: dict[str, list[str]] = {}
    for s, o in g.subject_objects(AMT.instanceOf):
        if str(o) not in concepts:
            undeclared.setdefault(str(o), []).append(str(s))
    for iri in sorted(undeclared):
        who = sorted(undeclared[iri])
        sample = ", ".join(_angle(x) for x in who[:3]) + (f" and {len(who) - 3} more" if len(who) > 3 else "")
        if iri == str(AMT.Concept):
            msg = (f"{sample} {'is' if len(who) == 1 else 'are'} declared as amt:instanceOf amt:Concept. "
                   "amt:Concept is the class of concepts, not a concept itself.")
            hint = ("Declare your own concept once and point to it:\n"
                    "<https://example.org/Coin> a amt:Concept ; rdfs:label \"Coin\" .\n"
                    f"{_angle(who[0])} amt:instanceOf <https://example.org/Coin> .")
        else:
            msg = (f"{_angle(iri)} is the target of amt:instanceOf ({sample}) "
                   "but is not declared as an amt:Concept, so those nodes are not loaded.")
            hint = f"Add:  {_angle(iri)} a amt:Concept ; rdfs:label \"...\" ."
        out.append(Finding("error", "AMT-E102", iri, msg, hint, related=tuple(who)))

    # ── E103: a weighted statement with a missing part ──────────────────
    for stmt in _weighted_statements(g):
        missing = [name for name, p in (("rdf:subject", RDF.subject),
                                        ("rdf:predicate", RDF.predicate),
                                        ("rdf:object", RDF.object))
                   if g.value(stmt, p) is None]
        if missing:
            out.append(Finding(
                "error", "AMT-E103", str(stmt),
                f"A statement with a weight lacks {', '.join(missing)}; it is ignored.",
                "A weighted edge needs rdf:subject, rdf:predicate, rdf:object and amt:weight (or fw:hasDegreeOfConnection) together.",
            ))

    # ── W201: weight outside [0, 1] ─────────────────────────────────────
    for stmt in _weighted_statements(g):
        for w in list(g.objects(stmt, AMT.weight)) + list(g.objects(stmt, FW.hasDegreeOfConnection)):
            try:
                value = float(w)
            except (TypeError, ValueError):
                continue
            if value < 0 or value > 1:
                out.append(Finding(
                    "warning", "AMT-W201", str(stmt),
                    f"Weight {value} is outside [0, 1].",
                    "Weights are degrees of truth between 0 and 1. The engine clamps values above 1 to 1.",
                ))

    # ── E104: amt:weight and fw:hasDegreeOfConnection disagree ──────────
    conflicts = []
    for stmt in _weighted_statements(g):
        a = [v for v in g.objects(stmt, AMT.weight)]
        b = [v for v in g.objects(stmt, FW.hasDegreeOfConnection)]
        if not a or not b:
            continue
        try:
            va, vb = float(a[0]), float(b[0])
        except (TypeError, ValueError):
            continue
        if abs(va - vb) > 1e-9:
            frm, role, to = (g.value(stmt, p) for p in (RDF.subject, RDF.predicate, RDF.object))
            if frm is not None and role is not None and to is not None:
                conflicts.append((str(frm), str(role), str(to), va, vb))
    for frm, role, to, va, vb in sorted(conflicts):
        out.append(Finding(
            "error", "AMT-E104", frm,
            f"The statement {_triple_text(frm, role, to)} has amt:weight {va} and fw:hasDegreeOfConnection {vb}; "
            "amt:weight is used.",
            "The two properties mean the same thing. Keep one of them, or give both the same value.",
        ))

    # ── W205: fw:hasType names something that is not one of the three types ─
    unknown_types: dict[str, list[str]] = {}
    for e in edges:
        t = e.get("type")
        if t and t not in KNOWN_TYPES:
            unknown_types.setdefault(t, []).append(_triple_text(e["from"], e["role"], e["to"]))
    for iri in sorted(unknown_types):
        who = sorted(unknown_types[iri])
        sample = "; ".join(who[:3]) + (f"; and {len(who) - 3} more" if len(who) > 3 else "")
        out.append(Finding(
            "warning", "AMT-W205", iri,
            f"{_angle(iri)} is used as fw:hasType ({sample}) but is not one of fw:Vagueness, fw:Uncertainty, "
            "fw:FuzzinessWobbliness. It is kept as it is and counted as its own type.",
            "Use one of the three individuals of the FW ontology (http://w3id.org/fw_ontology/), or leave fw:hasType out "
            "to get the default, fw:Vagueness.",
            related=tuple(who),
        ))

    # ── N303: a type without a method ───────────────────────────────────
    untyped_method = sorted(_triple_text(e["from"], e["role"], e["to"])
                            for e in edges if e.get("type") and not e.get("method"))
    if untyped_method:
        sample = "; ".join(untyped_method[:3]) + (f"; and {len(untyped_method) - 3} more" if len(untyped_method) > 3 else "")
        out.append(Finding(
            "note", "AMT-N303", untyped_method[0],
            f"{len(untyped_method)} statement(s) have fw:hasType but no fw:hasMethod ({sample}).",
            "Say how the weight was obtained, for example fw:hasMethod fw:EqualShareRule. "
            "Without a method the type is still used; nothing needs to be done.",
        ))

    # ── N301: edge role is not declared as an amt:Role ──────────────────
    used_roles = sorted({e["role"] for e in edges})
    undeclared_roles = [r for r in used_roles if r not in roles]
    for iri in undeclared_roles:
        out.append(Finding(
            "note", "AMT-N301", iri,
            f"Role {_angle(iri)} is used in edges but not declared as an amt:Role.",
            "That is fine as long as no axiom mentions it. To use it in axioms, declare:\n"
            f"{_angle(iri)} a amt:Role ; rdfs:label \"...\" ; rdfs:domain <...> ; rdfs:range <...> .",
        ))

    # ── N302: node without its own label ────────────────────────────────
    unlabelled = sorted(n for n in nodes if g.value(URIRef(n), RDFS.label) is None)
    if unlabelled:
        sample = ", ".join(_angle(x) for x in unlabelled[:3])
        more = f" and {len(unlabelled) - 3} more" if len(unlabelled) > 3 else ""
        out.append(Finding(
            "note", "AMT-N302", unlabelled[0],
            f"{len(unlabelled)} node(s) have no rdfs:label ({sample}{more}); the end of the IRI is shown instead.",
            "Add an rdfs:label to make the graph view readable.",
            related=tuple(unlabelled),
        ))

    # ── W204: nothing to reason about ───────────────────────────────────
    if not edges:
        out.append(Finding(
            "warning", "AMT-W204", "",
            "The file contains no weighted statement (nothing with amt:weight).",
            "AMT reasons over edges of the form  [] rdf:subject ... ; rdf:predicate ... ; rdf:object ... ; amt:weight 0.5 .\n"
            "Statements that are only linked with lado:hasAMT or similar are not read unless they carry these four properties.",
        ))

    order = {name: i for i, name in enumerate(LEVELS)}
    out.sort(key=lambda f: (order[f.level], f.code, f.subject))
    return out


def summarise(findings: list[Finding]) -> str:
    """One line such as ``2 error(s), 1 warning(s), 3 note(s)``."""
    counts = {lvl: sum(1 for f in findings if f.level == lvl) for lvl in LEVELS}
    return ", ".join(f"{counts[l]} {l}(s)" for l in LEVELS)


def has_errors(findings: list[Finding]) -> bool:
    return any(f.level == "error" for f in findings)

