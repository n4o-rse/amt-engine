"""
The How-To pages (``docs/howto/``): how to build an AMT file, how to check one and how to run it.

    howto/index.html      what to read first, which tool for which job
    howto/create/         build an AMT file from scratch or from other RDF (SPARQL CONSTRUCT)
    howto/validate/       check a file, read the messages, fix what they name
    howto/run/            run a file and look at the result, from cloning to the graph

Every piece of Turtle and SPARQL on these pages lives in ``EXAMPLES`` below, not in
the HTML text, so that ``tests/test_howto.py`` can run it: a "good" example must
validate and diagnose clean, a "bad" one must produce exactly the message the
page says it produces, and the CONSTRUCT must turn the sample data into a
file that passes. A how-to whose examples stop working fails the test suite.

The messages explained on the validate page are the ones of ``amt/diagnostics.py``
and ``ontology/amt-shapes.ttl``; ``CATALOGUE`` lists them and the test checks
that no code of the engine is missing from it.

All text is British English. No page contains a date of generation.
"""
from __future__ import annotations

from html import escape

try:
    from amt_site import page
except ImportError:
    from py.amt_site import page

PREFIXES = """@prefix amt:  <http://academic-meta-tool.xyz/vocab#> .
@prefix rdf:  <http://www.w3.org/1999/02/22-rdf-syntax-ns#> .
@prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .
@prefix xsd:  <http://www.w3.org/2001/XMLSchema#> .
@prefix ex:   <http://example.org/> .
"""

# --------------------------------------------------------------------------- #
# Examples (all of them are run by tests/test_howto.py)
# --------------------------------------------------------------------------- #
# kind "good": must pass SHACL and have no diagnostic error.
# kind "bad":  must produce the code(s) in "expect" (an AMT-... code, or "SHACL").
EXAMPLES = {
    "skeleton": {
        "kind": "good",
        "turtle": PREFIXES + """
# 1. Concepts: the kinds of things your file talks about
ex:Person a amt:Concept ;
    rdfs:label "Person" .

# 2. Nodes: every end of an edge, each one an instance of a concept
ex:ada     amt:instanceOf ex:Person ; rdfs:label "Ada Lovelace" .
ex:charles amt:instanceOf ex:Person ; rdfs:label "Charles Babbage" .
ex:mary    amt:instanceOf ex:Person ; rdfs:label "Mary Somerville" .

# 3. Edges: subject, role, object and a weight between 0 and 1
[] rdf:subject   ex:ada ;
   rdf:predicate ex:knows ;
   rdf:object    ex:charles ;
   amt:weight    "0.8"^^xsd:decimal .

[] rdf:subject   ex:charles ;
   rdf:predicate ex:knows ;
   rdf:object    ex:mary ;
   amt:weight    "0.6"^^xsd:decimal .
""",
    },
    "role": {
        "kind": "good",
        "turtle": PREFIXES + """
ex:Person a amt:Concept ; rdfs:label "Person" .
ex:ada     amt:instanceOf ex:Person ; rdfs:label "Ada" .
ex:charles amt:instanceOf ex:Person ; rdfs:label "Charles" .

# A role is optional until an axiom needs it. Then it names its domain and range.
ex:knows a amt:Role ;
    rdfs:label  "knows" ;
    rdfs:domain ex:Person ;
    rdfs:range  ex:Person .

[] rdf:subject ex:ada ; rdf:predicate ex:knows ; rdf:object ex:charles ; amt:weight 0.8 .

# An axiom: whoever knows someone who knows someone, knows that person a little (product logic)
ex:RCA a amt:RoleChainAxiom ;
    amt:antecedents ( ex:knows ex:knows ) ;
    amt:consequent  ex:knows ;
    amt:logic       amt:ProductLogic .
""",
    },
    # The case that started it all: the coins are nodes, the authorities are not.
    "bad-dangling": {
        "kind": "bad",
        "expect": "AMT-E101",
        "turtle": PREFIXES + """
ex:Coins a amt:Concept ; rdfs:label "Coins" .
ex:coin1 amt:instanceOf ex:Coins ; rdfs:label "coin 1" .

[] rdf:subject ex:coin1 ; rdf:predicate ex:hasAuthority ; rdf:object ex:vespasian ; amt:weight 0.5 .
ex:vespasian rdfs:label "vespasian" .          # a label does not make it a node
""",
    },
    "fixed-dangling": {
        "kind": "good",
        "turtle": PREFIXES + """
ex:Coins     a amt:Concept ; rdfs:label "Coins" .
ex:Authority a amt:Concept ; rdfs:label "Authority" .          # a second concept for the other end

ex:coin1     amt:instanceOf ex:Coins     ; rdfs:label "coin 1" .
ex:vespasian amt:instanceOf ex:Authority ; rdfs:label "vespasian" .     # now it is a node

[] rdf:subject ex:coin1 ; rdf:predicate ex:hasAuthority ; rdf:object ex:vespasian ; amt:weight 0.5 .
""",
    },
    "bad-concept-itself": {
        "kind": "bad",
        "expect": "SHACL",
        "turtle": PREFIXES + """
ex:coin1 amt:instanceOf amt:Concept ;          # wrong: amt:Concept is the class of concepts
    rdfs:label "coin 1" .
""",
    },
    "bad-no-label": {
        "kind": "bad",
        "expect": "SHACL",
        "turtle": PREFIXES + """
ex:Coins a amt:Concept .                       # no rdfs:label
ex:coin1 amt:instanceOf ex:Coins .
""",
    },
    "bad-undeclared-concept": {
        "kind": "bad",
        "expect": "SHACL",
        "turtle": PREFIXES + """
ex:coin1 amt:instanceOf ex:Coins .             # ex:Coins is never declared as a concept
""",
    },
    "bad-weight": {
        "kind": "bad",
        "expect": "SHACL",
        "turtle": PREFIXES + """
ex:C a amt:Concept ; rdfs:label "C" .
ex:a amt:instanceOf ex:C . ex:b amt:instanceOf ex:C .
[] rdf:subject ex:a ; rdf:predicate ex:r ; rdf:object ex:b ; amt:weight 1.5 .
""",
    },
    "bad-incomplete": {
        "kind": "bad",
        "expect": "AMT-E103",
        "turtle": PREFIXES + """
ex:C a amt:Concept ; rdfs:label "C" .
ex:a amt:instanceOf ex:C .
[] rdf:subject ex:a ; rdf:predicate ex:r ; amt:weight 0.5 .      # no rdf:object
""",
    },
}

# --------------------------------------------------------------------------- #
# The SPARQL recipe: other RDF -> AMT (the AFE case)
# --------------------------------------------------------------------------- #
CONSTRUCT_PREFIXES = """PREFIX amt:     <http://academic-meta-tool.xyz/vocab#>
PREFIX rdf:     <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
PREFIX rdfs:    <http://www.w3.org/2000/01/rdf-schema#>
PREFIX xsd:     <http://www.w3.org/2001/XMLSchema#>
PREFIX skos:    <http://www.w3.org/2004/02/skos/core#>
PREFIX nmo:     <http://nomisma.org/ontology#>
PREFIX nm:      <http://nomisma.org/id/>
PREFIX afe:     <http://afe.dainst.org/coin?afeid=>
PREFIX nfdi_fw: <http://w3id.org/fw_ontology/>
"""

CONSTRUCT_INPUT = """@prefix afe: <http://afe.dainst.org/coin?afeid=> .
@prefix nfdi_fw: <http://w3id.org/fw_ontology/> .
@prefix nm: <http://nomisma.org/id/> .
@prefix nmo: <http://nomisma.org/ontology#> .
@prefix rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#> .
@prefix skos: <http://www.w3.org/2004/02/skos/core#> .

# a coin that is either of two emperors (vague)
afe:15661 a nmo:NumismaticObject ;
    nmo:hasAuthority [ a nfdi_fw:VagueResourceValue, skos:Collection ;
        skos:member [ nfdi_fw:hasConfidence 0.5 ; rdf:value nm:vespasian ],
                    [ nfdi_fw:hasConfidence 0.5 ; rdf:value nm:titus ] ] .

# a coin with one certain emperor
afe:15668 a nmo:NumismaticObject ;
    nmo:hasAuthority nm:aurelian .

# a coin with one emperor, but only 60 % sure
afe:16048 a nmo:NumismaticObject ;
    nmo:hasAuthority [ a nfdi_fw:UncertainValue ;
        nfdi_fw:hasConfidence 0.6 ; rdf:value nm:philip_the_arab ] .

# a coin whose emperor is unknown: no edge, so it does not become a node
afe:11471 a nmo:NumismaticObject ;
    nmo:hasAuthority nm:uncertain_value .
"""

CONSTRUCT_QUERY = CONSTRUCT_PREFIXES + """
CONSTRUCT {
  # 1. Declare the concepts once, with labels
  afe:Coins    a amt:Concept ; rdfs:label "AFE coins" .
  nm:Authority a amt:Concept ; rdfs:label "Authority" .

  # 2. Make BOTH ends of every edge a node (this is the line people forget)
  ?coin      amt:instanceOf afe:Coins ;    rdfs:label ?coinLabel .
  ?authority amt:instanceOf nm:Authority ; rdfs:label ?authorityLabel .

  # 3. One weighted statement per edge
  ?edge rdf:subject   ?coin ;
        rdf:predicate nmo:hasAuthority ;
        rdf:object    ?authority ;
        amt:weight    ?weight .
}
WHERE {
  {
    # vague or combined values: one edge per candidate, with its confidence
    ?coin a nmo:NumismaticObject ; nmo:hasAuthority ?container .
    ?container skos:member ?candidate .
    ?candidate rdf:value ?authority ; nfdi_fw:hasConfidence ?weight .
  }
  UNION
  {
    # one value with a confidence
    ?coin a nmo:NumismaticObject ; nmo:hasAuthority ?container .
    ?container a nfdi_fw:UncertainValue ; rdf:value ?authority ; nfdi_fw:hasConfidence ?weight .
  }
  UNION
  {
    # a certain authority: weight 1. Only real IRIs; the containers above are blank nodes
    ?coin a nmo:NumismaticObject ; nmo:hasAuthority ?authority .
    FILTER(isIRI(?authority) && ?authority != nm:uncertain_value)
    BIND("1.0"^^xsd:decimal AS ?weight)
  }
  BIND(BNODE() AS ?edge)
  BIND(STRAFTER(STR(?coin), "?") AS ?coinLabel)
  BIND(STRAFTER(STR(?authority), "http://nomisma.org/id/") AS ?authorityLabel)
}
"""

# --------------------------------------------------------------------------- #
# The messages (CODE -> what it means). tests/test_howto.py checks that every code of
# amt/diagnostics.py appears here.
# --------------------------------------------------------------------------- #
CATALOGUE = [
    # (anchor, level, message, cause, fix, example key or None)
    ("AMT-E101", "error", "N IRI(s) are the subject or object of a weighted statement but are not AMT nodes",
     "An edge points at (or starts from) an IRI that has no amt:instanceOf. The reasoner cannot place it, so the "
     "edge cannot be followed or drawn. Giving the IRI an rdfs:label is not enough.",
     "Add amt:instanceOf and a concept to every IRI named in the message. If these IRIs are a different kind of thing "
     "than the others (coins and emperors, say), declare a second concept for them.",
     "bad-dangling"),
    ("AMT-E102", "error", "&lt;...&gt; is declared as amt:instanceOf amt:Concept / is the target of amt:instanceOf but is not declared as an amt:Concept",
     "amt:instanceOf must point at a concept of your own, and that concept must be declared with <code>a amt:Concept</code>. "
     "Pointing at amt:Concept itself, or at an IRI that is never declared, means those nodes are not loaded.",
     "Declare the concept once with a label and point to it.",
     "bad-undeclared-concept"),
    ("AMT-E103", "error", "A statement with amt:weight lacks rdf:subject / rdf:predicate / rdf:object",
     "A weighted edge needs all four properties together. A statement with a missing part is ignored.",
     "Add the missing property.",
     "bad-incomplete"),
    ("AMT-W201", "warning", "Weight X is outside [0, 1]",
     "Weights are degrees of truth between 0 and 1. SHACL rejects the file first, but with --no-validate the engine would clamp values above 1.",
     "Use a value between 0 and 1.",
     "bad-weight"),
    ("AMT-W204", "warning", "The file contains no weighted statement",
     "There is nothing to reason about. Typical reasons: the edges are written without amt:weight, or they are only linked "
     "from the nodes (for example with lado:hasAMT) and the reified statement itself is missing.",
     "Write each edge as a statement with rdf:subject, rdf:predicate, rdf:object and amt:weight.",
     None),
    ("AMT-N301", "note", "Role ... is used in edges but not declared as an amt:Role",
     "Fine for simple files. Only axioms need declared roles.",
     "Declare the role (label, domain, range) if you want to use it in an axiom.",
     None),
    ("AMT-N302", "note", "N node(s) have no rdfs:label",
     "The end of the IRI is shown instead, which is hard to read in the graph.",
     "Add an rdfs:label to the nodes.",
     None),
]

SHACL_MESSAGES = [
    ("Each Concept must have at least one rdfs:label.",
     "A concept has no label. The message names the IRI. Beware: every object of amt:instanceOf counts as a concept, "
     "so this message also appears when you write <code>amt:instanceOf amt:Concept</code> or point at an undeclared class.",
     "bad-no-label"),
    ("Each Role must have at least one rdfs:label. / exactly one rdfs:domain / exactly one rdfs:range.",
     "A role declared with <code>a amt:Role</code> needs a label, one domain and one range.", None),
    ("amt:weight must be a single xsd:decimal in the closed interval [0, 1].",
     "A weight is missing, doubled, not a number, or outside 0 to 1.", "bad-weight"),
    ("RoleChainAxiom must have exactly one amt:consequent / amt:logic ...",
     "An axiom lacks a part, or uses the legacy and the list form of antecedents at once. "
     "The messages for the other axiom types (inverse, subsumption, disjoint) work the same way.", None),
    ("RoleChainAxiom using amt:HamacherProduct must specify amt:logicParameter.",
     "The Hamacher operator needs its parameter: <code>amt:logicParameter 0.5</code>.", None),
]


# --------------------------------------------------------------------------- #
# helpers
# --------------------------------------------------------------------------- #
def _code(text: str) -> str:
    return f"<pre><code>{escape(text.strip(chr(10)))}</code></pre>"


def _ex(key: str, *, hide_prefixes: bool = True) -> str:
    text = EXAMPLES[key]["turtle"]
    if hide_prefixes and text.startswith(PREFIXES):
        text = text[len(PREFIXES):]
    return _code(text)


def _cards(items: list[tuple[str, str, str]]) -> str:
    """Link cards on the index page: (heading, text, href)."""
    return '<div class="cols">' + "".join(
        f'<div class="term"><h3><a href="{escape(h)}">{escape(t)}</a></h3><p>{x}</p></div>' for h, t, x in items
    ) + "</div>"


# --------------------------------------------------------------------------- #
# pages
# --------------------------------------------------------------------------- #
def howto_index() -> str:
    body = f"""
<h1>How-To</h1>
<p class="lead">Practical guides for working with AMT files: build one, check it, and understand what the messages mean.
Each guide starts from a small example you can copy.</p>

{_cards([
    ("create/", "Build an AMT file",
     "What an AMT file consists of, a complete file to start from, and how to turn existing RDF into AMT with a SPARQL CONSTRUCT query."),
    ("validate/", "Check an AMT file",
     "Run the checks, read what they say, and fix it. Every message is explained with the IRI it names, what causes it and what to add."),
    ("run/", "Run it and look at the result",
     "From nothing to a graph in your browser: clone the runner, where to put your file, which command to type, where the result appears."),
])}

<h2>The short version</h2>
<ol>
<li><strong>Declare concepts</strong> (<code>ex:Coin a amt:Concept ; rdfs:label "Coin"</code>).</li>
<li><strong>Make every end of every edge a node</strong> (<code>ex:c1 amt:instanceOf ex:Coin</code>), including the things your edges point <em>to</em>.</li>
<li><strong>Write edges</strong> as a statement with <code>rdf:subject</code>, <code>rdf:predicate</code>, <code>rdf:object</code> and <code>amt:weight</code>.</li>
<li><strong>Check</strong> before you reason: <code>python run_amt.py my.ttl --check-only</code>.</li>
<li><strong>Run</strong> and open the graph: <code>python run_amt.py my.ttl</code>, then <code>out\latest\my.html</code>.</li>
</ol>

<h2>Which tool for which job</h2>
<table>
<thead><tr><th>You want to&hellip;</th><th>Use</th></tr></thead>
<tbody>
<tr><td>try a file once, without installing anything but Python and git</td><td><a href="https://github.com/alpaca-fair-framework/amt-runner"><code>amt-runner</code></a> &rarr; <code>python run_amt.py my.ttl</code></td></tr>
<tr><td>check a file quickly while you build it</td><td><code>python run_amt.py my.ttl --check-only</code> (or <code>amt-runner my.ttl --check-only</code> with the engine installed)</td></tr>
<tr><td>run it inside your own Python project</td><td><code>pip install -e .</code> from <a href="https://github.com/alpaca-fair-framework/amt-engine">amt-engine</a>, then <code>from amt import load_amt, diagnose</code></td></tr>
<tr><td>look at the graph and the inferred edges</td><td>the HTML file of a run, or <a href="../explorer/">the Explorer</a> in your browser (<a href="run/">step by step</a>)</td></tr>
</tbody></table>
<p class="note">The two things called <em>amt-runner</em>: the repository <code>amt-runner</code> is a small wrapper
(<code>run_amt.py</code>) that fetches the engine for you; the engine itself also has a command <code>amt-runner</code>.
Both accept the same options.</p>
"""
    return page(title="How-To – AMT", body=body, depth=1, current="howto",
                description="How to build, check and fix an Academic Meta Tool data file.")


def howto_create() -> str:
    body = f"""
<h1>How to build an AMT file</h1>
<p class="lead">An AMT file is an ordinary Turtle file with three kinds of statements: concepts, nodes and weighted edges.
The most common mistake is to forget that <em>both ends</em> of an edge have to be nodes.</p>

<ul class="toc">
<li><a href="#parts">1. The parts</a></li>
<li><a href="#start">2. A complete file to start from</a></li>
<li><a href="#rules">3. Seven rules</a></li>
<li><a href="#roles">4. Roles and axioms (optional)</a></li>
<li><a href="#convert">5. From existing RDF with SPARQL CONSTRUCT</a></li>
<li><a href="#then">6. Then check it</a></li>
</ul>

<h2 id="parts">1. The parts</h2>
<table>
<thead><tr><th>Part</th><th>What it is</th><th>How you write it</th></tr></thead>
<tbody>
<tr><td><strong>Concept</strong></td><td>a kind of thing (Person, Coin, Authority)</td><td><code>ex:Coin a amt:Concept ; rdfs:label "Coin" .</code></td></tr>
<tr><td><strong>Node</strong></td><td>one thing of that kind</td><td><code>ex:c1 amt:instanceOf ex:Coin ; rdfs:label "coin 1" .</code></td></tr>
<tr><td><strong>Edge</strong></td><td>a relation between two nodes that holds to a degree</td><td>a statement with <code>rdf:subject</code>, <code>rdf:predicate</code>, <code>rdf:object</code>, <code>amt:weight</code></td></tr>
<tr><td>Role</td><td>names an edge type and says what it may connect (optional until an axiom needs it)</td><td><code>ex:knows a amt:Role ; rdfs:domain ex:Person ; rdfs:range ex:Person .</code></td></tr>
<tr><td>Axiom</td><td>a rule that derives new edges (optional)</td><td>see the <a href="../../ontology/">data model</a></td></tr>
</tbody></table>

<h2 id="start">2. A complete file to start from</h2>
<p>Copy this, replace the names, keep the structure. It passes every check.</p>
<p>Start with the prefixes. <code>ex:</code> stands for your own data; use your own namespace.</p>
{_code(PREFIXES)}
{_ex("skeleton")}

<h2 id="rules">3. Seven rules</h2>
<ol>
<li><strong>Every concept is declared</strong> with <code>a amt:Concept</code> and has an <code>rdfs:label</code>.</li>
<li><strong>Every end of every edge is a node</strong>: it has <code>amt:instanceOf</code>. This includes the thing an edge points <em>to</em>
(the emperor, the place, the other person). A label alone does not make it a node.</li>
<li><strong>Never write <code>amt:instanceOf amt:Concept</code>.</strong> amt:Concept is the class of concepts. Point at a concept of your own.</li>
<li><strong>An edge is a statement with four properties</strong>, all together. The subject and object must be IRIs, not literals.</li>
<li><strong>Weights are decimals from 0 to 1</strong> (<code>0.8</code> or <code>"0.8"^^xsd:decimal</code>). 1 means certain, 0 means not at all.</li>
<li><strong>Give nodes labels.</strong> Without one, the end of the IRI is shown, which is unreadable for IRIs like <code>.../coin?afeid=15661</code>.</li>
<li><strong>Extra triples are fine.</strong> AMT reads the parts above and ignores the rest. A link such as <code>lado:hasAMT</code> from a coin
to its edge statement is harmless and can stay; the engine finds edges by their <code>amt:weight</code>, not by that link.</li>
</ol>
<p class="note">Rule 2 is the one behind the error <a href="../validate/#AMT-E101"><code>AMT-E101</code></a>. This is what it looks like when it is broken, and the repair:</p>
<div class="cols" style="grid-template-columns:1fr">
<div class="term no"><h3>Broken</h3>{_ex("bad-dangling")}</div>
<div class="term"><h3>Fixed</h3>{_ex("fixed-dangling")}</div>
</div>

<h2 id="roles">4. Roles and axioms (optional)</h2>
<p>Edges work without declared roles. As soon as you write an axiom, the roles it names have to be declared with a label,
a domain and a range:</p>
{_ex("role")}
<p>All axiom types, with a figure and an example each, are on the <a href="../../ontology/">data model page</a>.</p>

<h2 id="convert">5. From existing RDF with SPARQL CONSTRUCT</h2>
<p>If your data is already RDF, you do not write the file by hand: a <code>CONSTRUCT</code> query produces it. The query has to
produce <strong>three things</strong>, in this order of importance:</p>
<ol>
<li>the <strong>concepts</strong>, declared with labels (once, as constant triples),</li>
<li><strong>both ends of every edge</strong> as nodes with <code>amt:instanceOf</code> and a label,</li>
<li>one <strong>weighted statement per edge</strong>.</li>
</ol>
<p>The example turns the vague and certain emperor attributions of the AFE coins into AMT. Sample input:</p>
{_code(CONSTRUCT_INPUT)}
<p>and the query:</p>
{_code(CONSTRUCT_QUERY)}
<p>Things to adapt: the two concept IRIs, the properties in <code>WHERE</code>, and how labels are made (here
<code>STRAFTER</code> takes the part of the IRI after a marker). <code>BNODE()</code> makes a fresh node for each edge statement.</p>
<p class="note">A <code>CONSTRUCT</code> that leaves out the second part (the authority nodes) is the typical cause of
<a href="../validate/#AMT-E101"><code>AMT-E101</code></a>: the coins are nodes, the emperors are not. Run the check on a small
sample first, then on the whole file.</p>

<h2 id="then">6. Then check it</h2>
<p>Save the result as <code>my.ttl</code> and continue with <a href="../validate/">how to check an AMT file</a>,
then <a href="../run/">run it and look at the result</a>.</p>
"""
    return page(title="Build an AMT file – How-To – AMT", body=body, depth=2, current="howto",
                description="How to write an Academic Meta Tool file: concepts, nodes, weighted edges, and how to generate one with SPARQL.")


def _catalogue_rows() -> str:
    rows = []
    for anchor, level, message, cause, fix, ex in CATALOGUE:
        example = f"<h4>Example</h4>{_ex(ex)}" if ex else ""
        rows.append(f"""<div class="term" id="{anchor}">
<h3><code>{anchor}</code> <span class="badge">{level}</span></h3>
<p><strong>{message}</strong></p>
<p><em>Cause.</em> {cause}</p>
<p><em>Fix.</em> {fix}</p>
{example}</div>""")
    return "\n".join(rows)


def _shacl_rows() -> str:
    rows = []
    for message, explanation, ex in SHACL_MESSAGES:
        example = _ex(ex) if ex else ""
        rows.append(f'<div class="term"><h3><code>{escape(message)}</code></h3><p>{explanation}</p>{example}</div>')
    return "\n".join(rows)


def howto_validate() -> str:
    body = f"""
<h1>How to check an AMT file</h1>
<p class="lead">Three checks, from "is it well formed" to "does it say what I meant". Run them while you build the file,
not after. Every message names the IRI it is about and says what to add.</p>

<ul class="toc">
<li><a href="#levels">1. What is checked</a></li>
<li><a href="#run">2. Run the check</a></li>
<li><a href="#read">3. Read the output</a></li>
<li><a href="#catalogue">4. The messages, one by one</a></li>
<li><a href="#exit">5. Exit codes</a></li>
<li><a href="#faq">6. Questions that come up</a></li>
</ul>

<h2 id="levels">1. What is checked</h2>
<table>
<thead><tr><th>Check</th><th>Question</th><th>Message looks like</th></tr></thead>
<tbody>
<tr><td><strong>Validation</strong> (SHACL)</td><td>Is the file well formed? Labels, weights, axioms complete?</td><td><code>FAIL Validation failed &hellip; [1] ex:Thing &hellip;</code></td></tr>
<tr><td><strong>Diagnostics</strong></td><td>Does it mean what you think? Are all edge ends nodes?</td><td><code>ERR [AMT-E101] &hellip;</code></td></tr>
<tr><td><strong>Consistency</strong></td><td>After reasoning, do the integrity axioms hold (disjoint roles, no reflexive roles)?</td><td><code>FAIL 2 consistency violation(s)</code></td></tr>
</tbody></table>
<p>The first two need no axioms and are what you want while building. The third only matters once you use axioms.</p>

<h2 id="run">2. Run the check</h2>
<p><strong>With the wrapper</strong> (needs Python and git; it fetches the engine itself):</p>
<pre><code>git clone https://github.com/alpaca-fair-framework/amt-runner
cd amt-runner
python run_amt.py my.ttl --check-only</code></pre>
<p>If you get <em>"does not know --check-only"</em> or a Python traceback, the engine copy cached in <code>.amt-cache/</code> is old:</p>
<pre><code>python run_amt.py my.ttl --check-only --update</code></pre>
<p><strong>With the engine installed</strong> (<code>pip install -e .</code> in <a href="https://github.com/alpaca-fair-framework/amt-engine">amt-engine</a>):</p>
<pre><code>amt-runner my.ttl --check-only
amt-runner my.ttl --check-only --strict
amt my.ttl --validate-only</code></pre>
<ul>
<li><code>--check-only</code> validates, loads and diagnoses, and <strong>writes nothing</strong>.</li>
<li><code>--strict</code> turns diagnostic errors into exit code 1, useful in scripts and CI.</li>
<li><code>amt --validate-only</code> runs only the SHACL validation.</li>
<li>A full run (<code>python run_amt.py my.ttl</code>) additionally reasons and writes Turtle, Cypher, CSV, an HTML graph and a report;
<a href="../run/">step by step, from cloning to the graph</a>.</li>
<li><code>--debug</code> shows the Python traceback if something unexpected fails.</li>
</ul>
<p><strong>In Python:</strong></p>
<pre><code>from amt import load_amt, diagnose
amt = load_amt("my.ttl")
for finding in diagnose(amt):
    print(finding.format())</code></pre>

<h2 id="read">3. Read the output</h2>
<p>A file whose emperors are not nodes (the case that prompted this page):</p>
<pre><code>VAL  Validating my.ttl ...
OK   Validation passed.
LOAD Loading my.ttl ...
OK   1 Concepts | 0 Roles | 4 Nodes | 7 Edges | 0 Axioms        &lt;- 4 nodes, but 7 edges that end somewhere else

DIAG 1 error(s), 0 warning(s), 1 note(s):
ERR  [AMT-E101] 7 IRI(s) are the subject or object of a weighted statement but are not AMT nodes: &lt;http://nomisma.org/id/aurelian&gt;, ...
  -&gt; Every end of an edge needs an amt:instanceOf &hellip; Add, for each, e.g.:
     &lt;http://nomisma.org/id/aurelian&gt; amt:instanceOf &lt;&hellip;&gt; ; rdfs:label "..." .</code></pre>
<p>Compare the counts in the <code>OK</code> line with what you expect: if there are far fewer <em>Nodes</em> than the things your edges
connect, some are not declared. A missing node is never silent any more, but a count that is too low is still the quickest hint.</p>
<p>Earlier versions of the engine stopped later with <code>AssertionError: non existent node ...</code> when drawing the graph.
That was this same problem; it is now reported up front, and the graph shows such IRIs as grey placeholder nodes.</p>

<h2 id="catalogue">4. The messages, one by one</h2>
<h3>Diagnostics</h3>
<div class="cols" style="grid-template-columns:1fr">
{_catalogue_rows()}
</div>
<h3 id="shacl">Validation (SHACL)</h3>
<p>These come from <a href="https://github.com/alpaca-fair-framework/amt-engine/blob/main/ontology/amt-shapes.ttl"><code>ontology/amt-shapes.ttl</code></a>.
The line above each message is the IRI it is about, followed by a hint on what to add.</p>
<div class="cols" style="grid-template-columns:1fr">
{_shacl_rows()}
</div>
<p>This is how a validation failure reads (two mistakes in one file):</p>
<pre><code>FAIL Validation failed with 2 violation(s):
  [1] amt:Concept
      Each Concept must have at least one rdfs:label.  (property: rdfs:label)
      -&gt; Add  amt:Concept rdfs:label "..." .  If this IRI is not meant to be a concept, check where it is used as the object of amt:instanceOf: &hellip;
  [2] ex:Thing
      Each Concept must have at least one rdfs:label.  (property: rdfs:label)
      -&gt; Add  ex:Thing rdfs:label "..." . &hellip;</code></pre>

<h2 id="exit">5. Exit codes</h2>
<table>
<thead><tr><th>Code</th><th>Meaning</th></tr></thead>
<tbody>
<tr><td><code>0</code></td><td>Done. Diagnostics may still have printed errors unless you used <code>--strict</code>; consistency violations of your axioms also leave this at 0.</td></tr>
<tr><td><code>1</code></td><td>The file did not pass validation, or <code>--strict</code> found a diagnostic error.</td></tr>
<tr><td><code>2</code></td><td>The input file was not found.</td></tr>
<tr><td><code>3</code></td><td>Something unexpected failed. Run with <code>--debug</code> and report it with the file, please.</td></tr>
</tbody></table>

<h2 id="faq">6. Questions that come up</h2>
<dl class="meta">
<dt>Is <code>lado:hasAMT</code> (or any other link from a node to its edge statement) right?</dt>
<dd>It does no harm. The engine finds edges by their <code>amt:weight</code> and reads the subject, predicate and object from the statement itself.
You can keep such a link for your own queries; AMT ignores it.</dd>
<dt>The checker says "OK" but the graph is empty or too small.</dt>
<dd>Look at the counts in the <code>OK</code> line and at the diagnostics. Zero edges usually means the statements have no <code>amt:weight</code>
(<a href="#AMT-W204"><code>AMT-W204</code></a>); too few nodes means <a href="#AMT-E101"><code>AMT-E101</code></a> or <a href="#AMT-E102"><code>AMT-E102</code></a>.</dd>
<dt>"Each Concept must have at least one rdfs:label", but I declared my concepts.</dt>
<dd>Every object of <code>amt:instanceOf</code> counts as a concept. The message names the IRI: it is either a concept of yours that lacks a label,
or something you pointed at by mistake (often <code>amt:Concept</code> itself).</dd>
<dt>Do I need roles?</dt>
<dd>Not until you write axioms. Undeclared roles show up as a harmless note (<a href="#AMT-N301"><code>AMT-N301</code></a>).</dd>
<dt>Does validation check my data against my own ontology?</dt>
<dd>No. It checks that the file is valid <em>AMT</em>. Whether your concepts and roles make sense for your domain is yours to decide.</dd>
<dt>It ends with a Python traceback.</dt>
<dd>Update the engine (<code>--update</code> with the wrapper, <code>git pull</code> otherwise) and run again. If it persists, run with <code>--debug</code>
and open an issue at <a href="https://github.com/alpaca-fair-framework/amt-engine/issues">amt-engine</a> with the file attached.</dd>
</dl>
"""
    return page(title="Check an AMT file – How-To – AMT", body=body, depth=2, current="howto",
                description="How to validate an Academic Meta Tool file, read the messages and fix what they name.")


# Files a full run writes (tests/test_howto.py compares this list with a real run).
RUN_OUTPUTS = [
    ("reasoned.ttl", "Your graph plus everything the rules inferred, as Turtle. Load this one into the Explorer."),
    ("html", "The interactive graph. Double-click it; it opens in your browser and works offline."),
    ("report.md", "A readable record of the run: validation, diagnostics, counts, every inferred edge, options."),
    ("nodes.csv", "One row per node, for spreadsheets."),
    ("edges.csv", "One row per edge with its weight, whether it was inferred, and which axioms produced it."),
    ("cypher", "The same graph as Neo4j Cypher statements, if you want it in a graph database."),
]


def howto_run() -> str:
    rows = "".join(f"<tr><td><code>&hellip;{escape(f)}</code></td><td>{escape(t)}</td></tr>" for f, t in RUN_OUTPUTS)
    # Python 3.10 does not allow a backslash inside the braces of an f-string, so the Windows path is made here.
    activate_cmd = _code(".venv\\Scripts\\activate")
    body = f"""
<h1>Run an AMT file and look at the result</h1>
<p class="lead">From nothing to a graph in your browser: what to install, what to clone, where to put your file,
which command to type and where the result appears. The commands are for the Windows command prompt;
Linux and macOS differences are noted.</p>

<ul class="toc">
<li><a href="#need">1. What you need</a></li>
<li><a href="#clone">2. Get the runner</a></li>
<li><a href="#file">3. Put your file somewhere</a></li>
<li><a href="#check">4. Check it</a></li>
<li><a href="#run">5. Run it</a></li>
<li><a href="#out">6. Find the result</a></li>
<li><a href="#graph">7. Look at the graph</a></li>
<li><a href="#explorer">8. Or use the Explorer</a></li>
<li><a href="#again">9. Change the file and run again</a></li>
<li><a href="#trouble">10. If something goes wrong</a></li>
</ul>

<h2 id="need">1. What you need</h2>
<p>Two programs, once:</p>
<ul>
<li><strong>Python 3.10 or newer.</strong> Check with <code>python --version</code> (on Windows <code>py --version</code> also works).</li>
<li><strong>git.</strong> Check with <code>git --version</code>.</li>
</ul>
<p>Nothing else: the runner fetches the engine and installs the three Python packages it needs
(<code>rdflib</code>, <code>pyshacl</code>, <code>pyvis</code>) the first time you run it.</p>

<h2 id="clone">2. Get the runner</h2>
<p>Open a command prompt in the folder where you keep your projects (for example <code>C:\\git</code>) and clone the runner:</p>
{_code("git clone https://github.com/alpaca-fair-framework/amt-runner.git")}
{_code("cd amt-runner")}
<p>Optional, but tidy: keep the packages out of your global Python with a virtual environment.</p>
{_code("python -m venv .venv")}
{activate_cmd}
<p class="note">Linux and macOS: <code>source .venv/bin/activate</code>. On recent Debian and Ubuntu a virtual environment is required.</p>

<h2 id="file">3. Put your file somewhere</h2>
<p>Anywhere you can name by path. Two easy choices:</p>
<ul>
<li><strong>Next to the runner:</strong> copy <code>my.ttl</code> into the <code>amt-runner</code> folder and use <code>my.ttl</code> in the commands below.</li>
<li><strong>Anywhere else:</strong> keep it where it is and give the path, for example <code>C:/tmp/my.ttl</code>
(forward slashes work on Windows; put the path in quotes if it contains spaces).</li>
</ul>
<p>The results are not written next to your file but into <code>amt-runner\\out\\</code> (section 6).
No file of yours is changed.</p>
<p>Not sure your file is an AMT file yet? <a href="../create/">How to build an AMT file</a> has a complete one to start from.</p>

<h2 id="check">4. Check it</h2>
<p>This validates and diagnoses and writes nothing, so it is the command to repeat while you build:</p>
{_code("python run_amt.py my.ttl --check-only")}
<p>The first time it also clones the engine into <code>.amt-cache\\</code> and installs the packages, which takes about half a minute.
You should see <code>OK Validation passed.</code> and a count such as <code>2 Concepts | 0 Roles | 11 Nodes | 7 Edges | 0 Axioms</code>.
If it prints <code>ERR</code> lines, fix them first: <a href="../validate/">how to check an AMT file</a> explains each one.</p>
<p><strong>Use <code>--update</code> now and then</strong>, and always after someone tells you the engine has changed. The runner keeps its own copy
of the engine and does not update it by itself:</p>
{_code("python run_amt.py my.ttl --check-only --update")}

<h2 id="run">5. Run it</h2>
<p>The same command without <code>--check-only</code>:</p>
{_code("python run_amt.py my.ttl")}
<p>It validates, loads, checks consistency, infers new edges with your axioms (none if you have no axioms), and writes the result.
The last lines of the output name the folder:</p>
<pre><code>&#10003; Outputs written to C:\\git\\amt-runner\\out\\run-20261027-130638
  (also accessible via C:\\git\\amt-runner\\out\\latest)</code></pre>

<h2 id="out">6. Find the result</h2>
<p>Every run gets its own folder <code>out\\run-&lt;date&gt;-&lt;time&gt;\\</code>, so earlier results are kept. <code>out\\latest\\</code> always points at
the newest one. The files are named after your file:</p>
<table><thead><tr><th>File</th><th>What it is</th></tr></thead><tbody>{rows}</tbody></table>

<h2 id="graph">7. Look at the graph</h2>
<p>Open <code>out\\latest\\my.html</code> by double-click. What you see:</p>
<ul>
<li><strong>One dot per node</strong>, coloured by its concept: all nodes of the first concept in orange, the second in blue, and so on.</li>
<li><strong>Arrows are edges</strong>, labelled <code>role: weight</code>. The thicker the arrow, the higher the weight.</li>
<li><strong>Red dashed arrows</strong> are edges the engine inferred from your axioms. Black ones are what you wrote.</li>
<li><strong>A grey dot</strong> is an IRI that an edge points to but that was never declared as a node. That is the problem
<a href="../validate/#AMT-E101"><code>AMT-E101</code></a> reports; add an <code>amt:instanceOf</code> for it.</li>
<li>Hover over a node for its concept, over an edge for <em>asserted</em> or <em>inferred</em>. Drag nodes to rearrange them, scroll to zoom.</li>
</ul>

<h2 id="explorer">8. Or use the Explorer</h2>
<p>The <a href="../../explorer/">AMT Explorer</a> loads a Turtle file and shows it in your browser. Open it, press the folder button and choose
<code>out\\latest\\my.reasoned.ttl</code>. It opens in your browser; the file is not uploaded anywhere.</p>

<h2 id="again">9. Change the file and run again</h2>
<ol>
<li>Edit <code>my.ttl</code>.</li>
<li><code>python run_amt.py my.ttl --check-only</code> until it is clean.</li>
<li><code>python run_amt.py my.ttl</code> for a new result in a new folder under <code>out\\</code>.</li>
</ol>
<p>Old run folders are never deleted by the runner. Delete the ones you do not need.</p>

<h2 id="trouble">10. If something goes wrong</h2>
<dl class="meta">
<dt><code>'git' is not recognized</code> / <code>'python' is not recognized</code></dt>
<dd>The program is not installed or not on the <code>PATH</code>. Install it, open a <em>new</em> command prompt and try again.
On Windows <code>py run_amt.py my.ttl</code> may work where <code>python</code> does not.</dd>
<dt><code>FAIL The cached AMT.engine does not know --check-only</code></dt>
<dd>The engine copy in <code>.amt-cache\\</code> is old. Add <code>--update</code>.</dd>
<dt>A Python traceback ending in <code>AssertionError</code> or something else</dt>
<dd>Almost always an old cached engine as well: add <code>--update</code>. If it stays, add <code>--debug</code> and
open an issue at <a href="https://github.com/alpaca-fair-framework/amt-engine/issues">amt-engine</a> with your file.</dd>
<dt><code>FAIL Validation failed</code></dt>
<dd>Your file is not valid AMT. Each message names the node and what to add: <a href="../validate/#shacl">the messages explained</a>.</dd>
<dt><code>ERR [AMT-E101]</code> or another code</dt>
<dd>Your file is valid but does not say what you probably meant. <a href="../validate/#catalogue">The messages explained</a>.</dd>
<dt>The graph is empty or has too few nodes</dt>
<dd>Look at the counts in the <code>OK</code> line and at the diagnostics; see the questions at the end of
<a href="../validate/#faq">how to check an AMT file</a>.</dd>
<dt>I have the engine installed and do not want the runner</dt>
<dd>With <code>pip install -e .</code> in a clone of <a href="https://github.com/alpaca-fair-framework/amt-engine">amt-engine</a> the same options work as
<code>amt-runner my.ttl --check-only</code> and <code>amt-runner my.ttl</code>; the result goes into an <code>out</code> folder next to your file.</dd>
</dl>
"""
    return page(title="Run an AMT file – How-To – AMT", body=body, depth=2, current="howto",
                description="Step by step: clone the runner, check and run an AMT file, find the result and look at the graph.")


PAGES = {
    "howto/index.html": howto_index,
    "howto/create/index.html": howto_create,
    "howto/validate/index.html": howto_validate,
    "howto/run/index.html": howto_run,
}
