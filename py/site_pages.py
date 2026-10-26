"""
The static pages of the vocabulary and the ontology.

``vocab_page`` is generated from ``ontology/amt.ttl``: every class, property,
logic operator and reasoning rule the ontology defines appears on it, with its
label, comment, domain and range. Nothing about a term is written twice. The
text around the terms (introduction, how to read) is prose in this file.

``ontology_page`` explains the data model: how an AMT file is put together.
Its Turtle examples live in ``SNIPPETS`` so that a test can parse and validate
every one of them; an example that stops being valid AMT fails the test suite.

All text is British English. No page contains a date of generation.
"""
from __future__ import annotations

from html import escape

from rdflib import RDF, RDFS, Graph, Literal, URIRef
from rdflib.namespace import OWL, SKOS, XSD

try:
    from amt_site import page
except ImportError:
    from py.amt_site import page

AMT = "http://academic-meta-tool.xyz/vocab#"
DCT = "http://purl.org/dc/terms/"
ONTOLOGY_IRI = URIRef("http://academic-meta-tool.xyz/vocab")

# The 25 terms of the 2018 vocabulary ("Penny Edition"). Every other term is
# marked "added since 2018" on the vocabulary page.
PENNY_TERMS = frozenset("""
Axiom Concept DisjointAxiom GoedelLogic InferenceAxiom IntegrityAxiom InverseAxiom Logic
LukasiewiczLogic ProductLogic Role RoleChainAxiom SelfDisjointAxiom antecedent antecedent1
antecedent2 consequent instanceOf inverse logic placeholder role role1 role2 weight
""".split())

PREFIXES = """@prefix amt:  <http://academic-meta-tool.xyz/vocab#> .
@prefix rdf:  <http://www.w3.org/1999/02/22-rdf-syntax-ns#> .
@prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .
@prefix xsd:  <http://www.w3.org/2001/XMLSchema#> .
@prefix ex:   <http://example.org/> .
"""

# (id, heading, Turtle). Shown on the ontology page, parsed and validated by tests/test_site.py.
SNIPPETS = {
    "concept": """ex:Person a amt:Concept ;
    rdfs:label "Person" ;
    amt:placeholder "Surname, forename" .

ex:ada amt:instanceOf ex:Person ;
    rdfs:label "Ada Lovelace" .

ex:charles amt:instanceOf ex:Person ;
    rdfs:label "Charles Babbage" .""",
    "role": """ex:connectedWith a amt:Role ;
    rdfs:label  "is connected with" ;
    rdfs:domain ex:Person ;
    rdfs:range  ex:Person .""",
    "quadruple": """[] rdf:subject   ex:ada ;
   rdf:predicate ex:connectedWith ;
   rdf:object    ex:charles ;
   amt:weight    "0.8"^^xsd:decimal .""",
    "rca": """ex:RCA a amt:RoleChainAxiom ;
    amt:antecedents ( ex:connectedWith ex:connectedWith ) ;
    amt:consequent  ex:connectedWith ;
    amt:logic       amt:ProductLogic .""",
    "rca-legacy": """ex:RCA2 a amt:RoleChainAxiom ;
    amt:antecedent1 ex:connectedWith ;
    amt:antecedent2 ex:connectedWith ;
    amt:consequent  ex:connectedWith ;
    amt:logic       amt:GoedelLogic .""",
    "rca-param": """ex:RCA3 a amt:RoleChainAxiom ;
    amt:antecedents ( ex:connectedWith ex:connectedWith ) ;
    amt:consequent  ex:connectedWith ;
    amt:logic       amt:HamacherProduct ;
    amt:logicParameter "0.5"^^xsd:decimal .""",
    "inverse": """ex:interestOf a amt:Role ;
    rdfs:label  "is interest of" ;
    rdfs:domain ex:Person ;
    rdfs:range  ex:Person .

ex:hasInterest a amt:Role ;
    rdfs:label  "has interest" ;
    rdfs:domain ex:Person ;
    rdfs:range  ex:Person .

ex:IA a amt:InverseAxiom ;
    amt:antecedent ex:interestOf ;
    amt:inverse    ex:hasInterest .""",
    "subsumption": """ex:before a amt:Role ;
    rdfs:label  "before" ;
    rdfs:domain ex:Person ;
    rdfs:range  ex:Person .

ex:older a amt:Role ;
    rdfs:label  "older" ;
    rdfs:domain ex:Person ;
    rdfs:range  ex:Person .

ex:SUB a amt:SubsumptionAxiom ;
    amt:subRole   ex:before ;
    amt:superRole ex:older .""",
    "disjoint": """ex:friendOf a amt:Role ;
    rdfs:label  "friend of" ;
    rdfs:domain ex:Person ;
    rdfs:range  ex:Person .

ex:enemyOf a amt:Role ;
    rdfs:label  "enemy of" ;
    rdfs:domain ex:Person ;
    rdfs:range  ex:Person .

ex:DA a amt:DisjointAxiom ;
    amt:role1 ex:friendOf ;
    amt:role2 ex:enemyOf .""",
    "self-disjoint": """ex:SDA a amt:SelfDisjointAxiom ;
    amt:role ex:enemyOf .""",
}


# --------------------------------------------------------------------------- #
# helpers
# --------------------------------------------------------------------------- #
def _lit(g: Graph, s, p) -> str:
    """The English value of a literal property, else any value, else ''."""
    vals = [o for o in g.objects(s, p) if isinstance(o, Literal)]
    for o in vals:
        if o.language == "en":
            return str(o)
    return str(sorted(vals, key=str)[0]) if vals else ""


def _local(iri: str) -> str:
    return iri[len(AMT):] if iri.startswith(AMT) else iri


_CURIES = {
    "http://www.w3.org/2000/01/rdf-schema#": "rdfs:",
    "http://www.w3.org/1999/02/22-rdf-syntax-ns#": "rdf:",
    "http://www.w3.org/2001/XMLSchema#": "xsd:",
    "http://www.w3.org/2002/07/owl#": "owl:",
}


def _curie(iri: str) -> str:
    if iri.startswith(AMT):
        return "amt:" + iri[len(AMT):]
    for ns, pre in _CURIES.items():
        if iri.startswith(ns):
            return pre + iri[len(ns):]
    return iri


def _ref(iri: str) -> str:
    """A link to the term's card when it is ours, plain code otherwise."""
    if iri.startswith(AMT):
        return f'<a href="#{escape(_local(iri))}"><code>{escape(_curie(iri))}</code></a>'
    return f"<code>{escape(_curie(iri))}</code>"


def _badge(local: str) -> str:
    return "" if local in PENNY_TERMS else '<span class="badge" title="Not part of the 2018 vocabulary">added since 2018</span>'


def _paras(text: str) -> str:
    return f"<p>{escape(text)}</p>" if text else ""


def _figure(svg: str, name: str, caption: str, base: str) -> str:
    return (f'<figure class="fig">{svg.rstrip()}'
            f'<figcaption>{escape(caption)} '
            f'<a href="{base}{name}.svg">SVG</a><a href="{base}{name}.png">PNG</a></figcaption></figure>')


def _classes_in_order(g: Graph) -> list[str]:
    """Depth-first over rdfs:subClassOf inside the AMT namespace, siblings by name."""
    classes = {str(c) for c in g.subjects(RDF.type, RDFS.Class) if str(c).startswith(AMT)}
    kids: dict[str, list[str]] = {}
    roots = []
    for c in sorted(classes):
        parents = [str(p) for p in g.objects(URIRef(c), RDFS.subClassOf) if str(p) in classes]
        if parents:
            for p in parents:
                kids.setdefault(p, []).append(c)
        else:
            roots.append(c)
    out: list[str] = []

    def walk(c: str) -> None:
        if c in out:
            return
        out.append(c)
        for k in sorted(kids.get(c, [])):
            walk(k)

    for r in roots:
        walk(r)
    return out


def _term_card(g: Graph, iri: str, extra_rows: list[tuple[str, str]] = ()) -> str:
    s = URIRef(iri)
    local = _local(iri)
    label = _lit(g, s, RDFS.label) or local
    comment = _lit(g, s, RDFS.comment)
    note = _lit(g, s, SKOS.note)
    rows = list(extra_rows)
    for pred, name in ((RDFS.subClassOf, "Subclass of"), (RDFS.domain, "Domain"), (RDFS.range, "Range")):
        vals = sorted(str(o) for o in g.objects(s, pred))
        if vals:
            rows.append((name, ", ".join(_ref(v) for v in vals)))
    dl = "".join(f"<dt>{escape(k)}</dt><dd>{v}</dd>" for k, v in rows)
    return (f'<div class="term" id="{escape(local)}"><h3>{escape(label)}{_badge(local)}</h3>'
            f'<div class="uri"><code>amt:{escape(local)}</code> &middot; {escape(iri)}</div>'
            f'{_paras(comment)}'
            + (f'<p><em>Note.</em> {escape(note)}</p>' if note else "")
            + (f"<dl>{dl}</dl>" if dl else "")
            + "</div>")


# --------------------------------------------------------------------------- #
# vocabulary page
# --------------------------------------------------------------------------- #
def vocab_page(g: Graph, overview_svg: str) -> str:
    onto = ONTOLOGY_IRI
    title = _lit(g, onto, URIRef(DCT + "title")) or "Academic Meta Tool Ontology"
    version = _lit(g, onto, OWL.versionInfo)
    created = _lit(g, onto, URIRef(DCT + "created"))
    creators = sorted(str(o) for o in g.objects(onto, URIRef(DCT + "creator")))
    licence = str(g.value(onto, URIRef(DCT + "license")) or "")
    source = str(g.value(onto, URIRef(DCT + "source")) or "")

    classes = _classes_in_order(g)
    cls_set = set(classes)
    props = sorted((str(p) for p in g.subjects(RDF.type, RDF.Property) if str(p).startswith(AMT)),
                   key=lambda p: (_prop_group(g, p, classes), _local(p)))
    logic_cls = URIRef(AMT + "Logic")
    logics = sorted(str(x) for x in g.subjects(RDF.type, logic_cls))
    rule_cls = URIRef(AMT + "ReasoningRule")
    rules = sorted(str(x) for x in g.subjects(RDF.type, rule_cls))
    new_terms = sorted(
        _local(str(s)) for s in set(g.subjects())
        if str(s).startswith(AMT) and len(str(s)) > len(AMT) and _local(str(s)) not in PENNY_TERMS
    )

    meta = [
        ("Namespace", f"<code>{escape(AMT)}</code>"),
        ("Edition", escape(version)),
        ("First published", f"{escape(created)} (the 2018 &ldquo;Penny Edition&rdquo;)"),
        ("Authors", escape(" & ".join(creators))),
        ("Licence", f'<a href="{escape(licence)}">CC BY 4.0</a> (as published since 2018)' if licence else ""),
        ("Based on", f'Unold, Thiery, Mees (2019), <a href="{escape(source)}">Academic Meta Tool. Ein Web-Tool zur Modellierung von Vagheit</a>, ZfdG Sonderband 4' if source else ""),
        ("Download", '<a href="amt.ttl">Turtle</a> &middot; <a href="amt.rdf">RDF/XML</a> &middot; <a href="amt.jsonld">JSON-LD</a>'),
    ]
    meta_html = "".join(f"<dt>{k}</dt><dd>{v}</dd>" for k, v in meta if v)

    toc = ('<ul class="toc"><li><a href="#classes">Classes</a></li><li><a href="#properties">Properties</a></li>'
           '<li><a href="#logics">Fuzzy logics</a></li><li><a href="#rules">Reasoning rules</a></li>'
           '<li><a href="#changes">Changes since 2018</a></li></ul>')

    parts = [
        f"<h1>{escape(title.replace('Ontology', 'Vocabulary'))}</h1>",
        '<p class="lead">The terms of the Academic Meta Tool (AMT): the classes and properties for '
        'modelling relations that hold only to a degree, the axioms that derive new relations from existing ones, '
        'and the fuzzy logics that combine their weights.</p>',
        f'<dl class="meta">{meta_html}</dl>',
        toc,
        "<h2 id=\"overview\">Overview</h2>",
        _figure(overview_svg, "amt-overview", "Classes, subclass links and the properties between them, drawn from amt.ttl.", ""),
        '<p>How the terms fit together in a data file is explained on the <a href="../ontology/">ontology page</a>.</p>',
        '<h2 id="classes">Classes</h2>',
    ]
    for c in classes:
        parts.append(_term_card(g, c))
    parts.append('<h2 id="properties">Properties</h2>')
    for p in props:
        parts.append(_term_card(g, p))
    parts.append('<h2 id="logics">Fuzzy logics</h2>'
                 '<p>An axiom names one of these operators in <code>amt:logic</code>. The operator combines the weights '
                 'of the edges along a chain into the weight of the inferred edge.</p>')
    rows = []
    for l in logics:
        s = URIRef(l)
        loc = _local(l)
        rows.append(
            f'<tr id="{escape(loc)}"><td><strong>{escape(_lit(g, s, RDFS.label) or loc)}</strong>{_badge(loc)}'
            f'<br><code>amt:{escape(loc)}</code></td><td><code>{escape(_lit(g, s, URIRef(AMT + "formula")))}</code></td>'
            f'<td>{escape(_lit(g, s, URIRef(AMT + "arity")))}</td>'
            f'<td>{escape(_lit(g, s, RDFS.comment))} {escape(_lit(g, s, URIRef(AMT + "recommendedFor")))}</td></tr>')
    parts.append('<table><thead><tr><th>Operator</th><th>Formula</th><th>Arity</th><th>Behaviour and use</th></tr></thead>'
                 f'<tbody>{"".join(rows)}</tbody></table>')
    parts.append('<h2 id="rules">Reasoning rules</h2>'
                 '<p>RDFS cannot express arithmetic, so what a reasoner must do is described as data: '
                 'each rule names the axiom it belongs to, when it applies and what it adds or reports. '
                 'An implementation in another language can be derived from this list.</p>')
    for r in rules:
        s = URIRef(r)
        applies = g.value(s, URIRef(AMT + "appliesTo"))
        rows2 = []
        if applies is not None:
            rows2.append(("Applies to", _ref(str(applies))))
        pre = _lit(g, s, URIRef(AMT + "precondition"))
        eff = _lit(g, s, URIRef(AMT + "effect"))
        if pre:
            rows2.append(("Precondition", escape(pre)))
        if eff:
            rows2.append(("Effect", escape(eff)))
        parts.append(_term_card(g, r, rows2))
    parts.append('<h2 id="changes">Changes since 2018</h2>'
                 '<p>The 2018 vocabulary ("Penny Edition") had 25 terms. All of them are still here with the same '
                 'identifiers; nothing was removed or renamed. What changed:</p><ul>'
                 f'<li><strong>{len(new_terms)} new terms</strong>, marked on their cards: '
                 + ", ".join(f"<code>{escape(t)}</code>" for t in new_terms) + ".</li>"
                 '<li>The fuzzy operators are <strong>instances</strong> of <code>amt:Logic</code> with a formula, '
                 'an arity and a usage hint. In the 2018 RDF file they were modelled as classes.</li>'
                 '<li>Terms are typed as <code>rdfs:Class</code> and <code>rdf:Property</code> only. The 2018 RDF/XML '
                 'also typed them as <code>owl:Class</code>, <code>owl:ObjectProperty</code> and '
                 '<code>owl:DatatypeProperty</code>.</li>'
                 '<li>The ontology resource is <code>http://academic-meta-tool.xyz/vocab</code> (without the hash).</li>'
                 '</ul>')
    return page(title=f"{title.replace('Ontology', 'Vocabulary')} – AMT", body="\n".join(parts),
                depth=1, current="vocab",
                description="Classes, properties, fuzzy logics and reasoning rules of the Academic Meta Tool vocabulary.")


def _prop_group(g: Graph, p: str, classes: list[str]) -> int:
    """Order properties by the position of their domain class; no domain goes last."""
    dom = g.value(URIRef(p), RDFS.domain)
    if dom is not None and str(dom) in classes:
        return classes.index(str(dom))
    return len(classes)


# --------------------------------------------------------------------------- #
# ontology page
# --------------------------------------------------------------------------- #
def _code(key: str) -> str:
    return f'<pre><code>{escape(SNIPPETS[key])}</code></pre>'


def ontology_page(g: Graph, figures: dict[str, str]) -> str:
    def fig(name: str, caption: str) -> str:
        return _figure(figures[name], name, caption, "img/")

    logics = sorted(str(x) for x in g.subjects(RDF.type, URIRef(AMT + "Logic")))
    logic_rows = "".join(
        f'<tr><td><code>amt:{escape(_local(l))}</code></td><td><code>{escape(_lit(g, URIRef(l), URIRef(AMT + "formula")))}</code></td>'
        f'<td>{escape(_lit(g, URIRef(l), URIRef(AMT + "arity")))}</td></tr>' for l in logics)

    body = f"""
<h1>The AMT data model</h1>
<p class="lead">An AMT file describes a graph whose edges hold only to a degree. This page shows how such a file is put
together: the building blocks, the axioms that derive new edges, and a small Turtle example for each. Every example on this
page is parsed and validated against the SHACL shapes whenever the test suite runs.</p>

<p>All examples assume these prefixes. <code>ex:</code> stands for your own data.</p>
<pre><code>{escape(PREFIXES.strip())}</code></pre>

<h2 id="concepts">Concepts and individuals</h2>
<p>A <strong>Concept</strong> is a class of things in your domain, such as Person or Place. Individuals are linked to
their Concept with <code>amt:instanceOf</code>. The optional <code>amt:placeholder</code> tells an editor what a label
should look like.</p>
{fig("concept", "An individual is an instance of a Concept; the Concept has the type amt:Concept.")}
{_code("concept")}

<h2 id="roles">Roles</h2>
<p>A <strong>Role</strong> is a typed relation between two Concepts, the label of an edge. It declares its domain and range.</p>
{fig("role", "A Role relates the Concepts of its domain and range.")}
{_code("role")}

<h2 id="edges">Weighted edges</h2>
<p>An edge is a quadruple: a subject, a role, an object and a weight between 0 and 1 in <code>amt:weight</code>.
It is written as a reified statement, so that the weight has something to attach to.</p>
{fig("quadruple", "A weighted edge: subject, role, object and weight in [0;1].")}
{_code("quadruple")}

<h2 id="axioms">Axioms</h2>
<p>Axioms are statements about roles, not about individuals. Inference axioms derive new edges, integrity axioms
describe edges that must not exist.</p>

<h3 id="rca">Role chain axiom</h3>
<p>If a chain of edges exists, an edge between its two ends is inferred. Its weight is computed from the weights along the
chain by the fuzzy logic named in <code>amt:logic</code>. <code>amt:antecedents</code> takes a list of any length; the
older two-step form with <code>amt:antecedent1</code> and <code>amt:antecedent2</code> is still valid.</p>
{fig("rca", "Two steps: the consequent holds between the two ends of the chain.")}
{_code("rca")}
{fig("rca-nary", "A chain of n steps.")}
{_code("rca-legacy")}
<p>Parametrised operators take their parameter from <code>amt:logicParameter</code>:</p>
{_code("rca-param")}

<h3 id="inverse">Inverse axiom</h3>
<p>An edge with the antecedent role implies the reverse edge with the inverse role, at the same weight.</p>
{fig("ia", "Two roles that are the inverse of each other.")}
{_code("inverse")}

<h3 id="subsumption">Subsumption axiom</h3>
<p>One role is finer than another: every edge with the sub-role is also an edge with the super-role, at the same weight.
Only the direct step is declared; the engine computes the transitive closure.</p>
{fig("subsumption", "Every edge of the sub-role also carries the super-role.")}
{_code("subsumption")}

<h3 id="disjoint">Disjoint axiom</h3>
<p>Two roles must not hold between the same pair of nodes. The engine reports a violation if they do.</p>
{fig("da", "Two roles that exclude each other.")}
{_code("disjoint")}

<h3 id="self-disjoint">Self-disjoint axiom</h3>
<p>A role must not hold between a node and itself.</p>
{fig("sda", "A role that is never reflexive.")}
{_code("self-disjoint")}

<h2 id="logics">Fuzzy logics</h2>
<p>The operators below combine the weights along a chain. Which one fits depends on how you want the length of a chain to
count; the <a href="../vocab/#logics">vocabulary page</a> has a usage hint for each.</p>
<table><thead><tr><th>Operator</th><th>Formula</th><th>Arity</th></tr></thead><tbody>{logic_rows}</tbody></table>

<h2 id="validation">Checking a file</h2>
<p>The shapes in <a href="https://github.com/n4o-rse/amt-engine/blob/main/ontology/amt-shapes.ttl"><code>ontology/amt-shapes.ttl</code></a>
check that weights lie in [0, 1], that axioms have the properties they need and that role chains do not mix the two
forms. The AMT engine runs them before it loads a file.</p>
"""
    return page(title="The AMT data model – AMT", body=body, depth=1, current="ontology",
                description="How an Academic Meta Tool data file is built: concepts, roles, weighted edges and axioms.")
