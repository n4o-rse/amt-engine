# AMT.engine

**Academic Meta Tool — Reasoning Engine**

A pure-Python reasoner for the [Academic Meta Tool](http://academic-meta-tool.xyz/)
ontology. Reads a Turtle file with concepts, roles and weighted assertions,
applies fuzzy-logic role-chain inference and integrity checks, and exports
the resulting graph as RDF, Cypher, CSV or interactive HTML.

## Features

- **SHACL pre-validation** of input files against the bundled
  `ontology/amt-shapes.ttl`. Catches malformed axioms before they reach
  the reasoner.
- **n-ary RoleChainAxioms** via `amt:antecedents` (an RDF list of
  arbitrary length). Legacy 2-step `antecedent1`/`antecedent2` form is
  also accepted.
- **Role subsumption** via `amt:SubsumptionAxiom`, for vocabularies whose
  roles are sets of finer roles. Either spelled out as entailment
  (default) or used to strip redundant conclusions (`--minimal`).
- **Six fuzzy-logic operators** through one unified `aggregate_weights`
  API, registry-based for easy extension: Gödel, Product, Łukasiewicz,
  Einstein, Geometric Mean, Hamacher.
- **Provenance tracking** — every inferred edge knows which axiom IRIs
  contributed to its derivation. When an edge can be reached through
  multiple axioms, their IRIs are merged into a single provenance list.
- **Four output formats** — RDF/Turtle (round-trip-compatible),
  Neo4J Cypher, two-file CSV (nodes + edges) and a self-contained
  interactive HTML graph.
- **Markdown run reports** that document every pipeline run alongside
  its outputs, so old result folders stay self-describing.

## Architecture

![AMT architecture](AMT_architecture.png)

The Mermaid source for this diagram is at
[`amt/architecture.mmd`](amt/architecture.mmd). Re-render with
[mermaid.live](https://mermaid.live) or any local `mmdc` install.

## Layout

```
amt/                        pip-installable package
├── __init__.py             public API re-exports
├── core.py                 load_amt, parser only
├── reasoning.py            do_reasoning, check_consistency
├── subsumption.py          role hierarchy: closure + redundancy removal
├── logic.py                aggregate_weights, LOGIC_REGISTRY
├── _resources.py           locates the bundled ontology/ folder
├── validation.py           validate_against_shapes (SHACL wrapper)
├── export.py               export_ttl, export_cypher, export_csv
├── viz.py                  pyvis HTML visualisation
├── cli.py                  the `amt` command
├── runner.py               the `amt-runner` command (full pipeline)
└── architecture.mmd        Mermaid source for the diagram above

ontology/                   formal AMT specification
├── amt.ttl                 vocabulary
├── amt-shapes.ttl          SHACL shapes
├── examples/               valid + invalid example data files
└── validate_examples.py    standalone validation demo

docs/                       webviewer (GitHub Pages) and its sample data
examples/                   sample TTL inputs to play with
tests/                      pytest test suite

main.py                     development pipeline (see "Development")
py/                         the steps behind main.py
PRIMER.md                   work plan and decisions (German)
CHANGELOG.md                what changed in which version
CITATION.cff                how to cite this software
pyproject.toml              build config + entry points
requirements.txt            runtime dependencies (mirrors pyproject)
requirements-dev.txt        the above plus pytest
.github/workflows/          ci.yml (pipeline on push and pull request), sync-examples-to-docs.yml
```

`ontology/` stays at the repository root, where the ontology README, the
diagrams and `validate_examples.py` expect it. `pyproject.toml` maps it
into the package namespace at build time, so an *installed* AMT carries
the vocabulary as `amt/ontology/` rather than claiming a generic
top-level `ontology/` directory in `site-packages`.

## Quickstart

```bash
git clone <repo-url> amt.engine
cd amt.engine
python -m venv .venv
. .venv/bin/activate                   # Windows: .\.venv\Scripts\activate
pip install -e ".[dev]"
pytest tests/ -q                       # all green
```

If you vendor the source tree instead of installing it — a CI image, a
Docker layer, a wrapper such as `amt.runner` that clones the repository —
use the requirements files instead:

```bash
pip install -r requirements-dev.txt
```

Then run the bundled animals example through the full pipeline:

```bash
amt-runner examples/animals.ttl
# or, equivalently:
python -m amt.runner examples/animals.ttl
```

This validates the file, loads it, runs the consistency check and the
reasoner, then writes six files into `examples/out/`:

```
animals.reasoned.ttl     RDF/Turtle, asserted + inferred
animals.cypher           Neo4J Cypher
animals.nodes.csv        flat tabular nodes
animals.edges.csv        flat tabular edges (with provenance)
animals.html             interactive graph
animals.report.md        human-readable run report
```

The output folder is cleared at the start of every run, so it always
reflects the most recent pipeline.

## What the pipeline does

1. **Validate** the input against `ontology/amt-shapes.ttl` (SHACL).
   Refuses to proceed on a malformed file.
2. **Load** the data: parse Concepts, Roles, Nodes, Edges and Axioms.
   The bundled `ontology/amt.ttl` is loaded automatically as an RDFS
   inference graph, so input files don't need to redeclare the vocabulary.
3. **Reason** to a fixed point: every RoleChain and Inverse axiom is
   applied iteratively until no new edges are produced.
4. **Check consistency** by evaluating Disjoint and SelfDisjoint axioms
   against the reasoned edge set.
5. **Export** the result as TTL, Cypher, CSV and HTML.
6. **Write a Markdown run report** documenting what happened.

## Library use

```python
from amt import load_amt, do_reasoning, check_consistency, export_csv

amt = load_amt("my-data.ttl", validate=True)        # raises if invalid
reasoned = do_reasoning(amt["edges"], amt["axioms"])
inferred = [e for e in reasoned if e["inferred"]]

ok, violations = check_consistency(amt["edges"], amt["axioms"])

nodes_csv, edges_csv = export_csv(
    amt["nodes"], amt["edges"], amt["axioms"],
    "output/", with_reasoning=True, prefix="my-data",
)
```

For the full pipeline in one call:

```python
from amt.runner import run_all
amt = run_all("my-data.ttl", output_dir="out/")
```

Each inferred edge has an `inferred=True` flag and a `provenance` list
of axiom IRIs. Asserted edges have `inferred=False` and an empty
provenance list.

## CLI

The `amt` command is flag-driven — use it for selective steps:

```bash
amt input.ttl --validate-only                 # just SHACL check, exit 0/1
amt input.ttl --info                          # print ontology summary
amt input.ttl --reason --check                # reason + integrity check
amt input.ttl --reason --minimal              # drop subsumed conclusions
amt input.ttl --reason \
    --export-ttl out.ttl \
    --export-csv out/ \
    --export-cypher out.cypher \
    --export-html graph.html
```

The `amt-runner` command runs everything at once and writes a report.
Use the equivalent `python -m amt.runner` form if you don't want to rely
on the installed entry point. It takes `--minimal` too.

## Role subsumption

Some vocabularies define roles as *sets* of finer roles — Freksa's
semi-interval relations, for instance, where `ob` = {`<`, `m`, `o`} and
`ol` = {`<`, `m`, `o`, `fi`, `di`}. Set inclusion then gives chains of
proper subset relations, and a reasoner that does not know about them
derives every member of a chain independently. All are true; all but the
finest are redundant.

`amt:SubsumptionAxiom` states the relation between two roles, in the same
way `amt:InverseAxiom` does:

```turtle
ex:SUB1 a amt:SubsumptionAxiom ;
    amt:subRole   ex:before ;
    amt:superRole ex:olderBeginning .
```

Read as: every `before` edge is also an `olderBeginning` edge, at no lower
weight. Only the covering relation needs declaring — the engine computes
the transitive closure itself.

Two readings, and the caller picks one:

| Mode | Effect |
|------|--------|
| default | **Entailment.** Every `subRole` edge yields a `superRole` edge at the same weight, so the hierarchy is spelled out for consumers that do not know it. Increases the edge count. |
| `--minimal` / `do_reasoning(..., minimal=True)` | **Redundancy elimination.** No entailment; after the fixed point, an inferred edge is dropped when a finer edge relates the same pair at no lower weight. |

Suppression requires `weight(fine) ≥ weight(coarse)`. A coarse relation
derived along a strong path can be worth more than a fine relation derived
along a weak one, so when the fine edge is weaker both are kept. Asserted
edges are never suppressed, and `--minimal` runs the consistency check on
the reduced graph — a `DisjointAxiom` over a coarse role will not fire on
an edge that was removed.

Files without `SubsumptionAxiom` behave identically in both modes.
[`examples/subsumption-demo.md`](examples/subsumption-demo.md) works
through every inference in both.

## Fuzzy-logic operators

Pick any of the six operators with `amt:logic` on a `RoleChainAxiom`:

```turtle
ex:RCA a amt:RoleChainAxiom ;
    amt:antecedents ( ex:knows ex:trusts ex:knows ) ;
    amt:consequent  ex:trusts ;
    amt:logic       amt:GeometricMean .         # n-ary, no parameter

ex:RCA_Hamacher a amt:RoleChainAxiom ;
    amt:antecedents    ( ex:knows ex:trusts ) ;
    amt:consequent     ex:trusts ;
    amt:logic          amt:HamacherProduct ;
    amt:logicParameter "2.0"^^xsd:decimal .     # gamma > 1 = softer than product
```

| Operator              | Arity   | Recommended for          |
|-----------------------|---------|--------------------------|
| `amt:GoedelLogic`     | binary  | curated mappings, n=2..3 |
| `amt:ProductLogic`    | binary  | independent evidence, n=2 |
| `amt:LukasiewiczLogic`| binary  | strict reasoning, n=2 only |
| `amt:EinsteinProduct` | binary  | medium-confidence, n=3..4 |
| `amt:GeometricMean`   | n-ary   | comparing chains, n≥4 |
| `amt:HamacherProduct` | binary  | tunable, research |

Adding a new operator means one entry in `amt/logic.py`'s
`LOGIC_REGISTRY` plus a matching `amt:Logic` instance in
`ontology/amt.ttl`. See the [ontology README](ontology/README.md)
for the full vocabulary specification.

## Input format at a glance

A minimal AMT data file declares concepts, roles, instances, weighted
assertions and at least one axiom:

```turtle
@prefix amt:  <http://academic-meta-tool.xyz/vocab#> .
@prefix rdf:  <http://www.w3.org/1999/02/22-rdf-syntax-ns#> .
@prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .
@prefix xsd:  <http://www.w3.org/2001/XMLSchema#> .
@prefix ex:   <http://example.com/> .

ex:Person a amt:Concept ;
    rdfs:label "Person" ;
    amt:placeholder "Lastname, Firstname" .

ex:knows a amt:Role ;
    rdfs:label "knows" ;
    rdfs:domain ex:Person ;
    rdfs:range  ex:Person .

ex:alice amt:instanceOf ex:Person ; rdfs:label "Alice" .
ex:bob   amt:instanceOf ex:Person ; rdfs:label "Bob" .

_:a1 rdf:subject   ex:alice ;
     rdf:predicate ex:knows ;
     rdf:object    ex:bob ;
     amt:weight    "0.9"^^xsd:decimal .

ex:RCA a amt:RoleChainAxiom ;
    amt:antecedents ( ex:knows ex:knows ) ;
    amt:consequent  ex:knows ;
    amt:logic       amt:GoedelLogic .
```

The `ontology/` folder defines the full vocabulary and SHACL shapes —
any tool that wants to consume or produce AMT-compatible data can rely
on those files alone.

## Bundled examples

| File | Purpose |
|------|---------|
| `examples/chain-test.ttl` | Minimal Alice/Bob/Carol/Dave chain — useful for understanding what reasoning produces from a simple input. |
| `examples/subsumption-demo.ttl` | Six events and a three-role subsumption chain (`before ⊑ olderBeginning ⊑ older`), a miniature of Freksa's semi-interval vocabulary. Run it with and without `--minimal` to see both readings of `amt:SubsumptionAxiom`; the companion file [`examples/subsumption-demo.md`](examples/subsumption-demo.md) documents every derivation. |
| `examples/animals.ttl` | Taxonomy meets family tree: seven species, three animal families across 5/3/3 generations, four `RoleChainAxiom`s using Goedel, Product and Geometric Mean. The companion file [`examples/animals.md`](examples/animals.md) documents the family-tree diagrams and lists every expected derivation. |
| `ontology/examples/example-valid.ttl` | Smallest possible file that passes SHACL validation. |
| `ontology/examples/example-invalid.ttl` | Deliberately broken file used in the validation tests; produces exactly four expected SHACL violations. |

## Development

`python main.py` runs the maintenance pipeline: it checks that version,
date and changelog agree, validates the bundled SHACL examples, runs the test
suite, pushes every example through the full pipeline, confirms that two runs
under different hash seeds produce identical bytes, and syncs `examples/*.ttl`
to `docs/data/`.

```bash
python main.py                     # all steps
python main.py --list              # show the steps
python main.py --only tests        # one step
python main.py --from examples     # this step and everything after
python main.py --dry-run           # print the plan, run nothing
python main.py --strict            # warnings become errors (use this in CI)
```

GitHub Actions runs `python main.py --strict` on every push to `main` and on
every pull request (`.github/workflows/ci.yml`), on Linux and Windows with
Python 3.10 and 3.13. The report of each job is kept as a workflow artefact.

The combined output is written to `build/pipeline_report.txt`. The product
commands `amt` and `amt-runner` are independent of `main.py`. Changes are
recorded in [`CHANGELOG.md`](CHANGELOG.md); `PRIMER.md` holds the (German)
work plan and the decisions behind the repository.

## Acknowledgements

AMT.engine is developed within
[**mainzed**](https://www.mainzed.org/) — Mainzer Zentrum für Digitalität
in den Geistes- und Kulturwissenschaften — at
[Hochschule Mainz, i3mainz](https://i3mainz.hs-mainz.de/)
and the [Leibniz-Zentrum für Archäologie (LEIZA)](https://www.leiza.de/).

This work is part of the DFG-funded NFDI initiative, specifically the
[Research Data Infrastructure for the Material Remains of Human History
(NFDI4Objects)](https://www.nfdi4objects.net/) — DFG project number
**501836407**.

## AI usage

Parts of the Python code in this repository were written with the assistance of
Claude (Anthropic). All AI-assisted code was reviewed, validated and supervised
by Florian Thiery (research software engineering).
