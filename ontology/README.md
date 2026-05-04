# AMT Ontology

Formal vocabulary, axiom structures and reasoning rules for the
[Academic Meta Tool](http://academic-meta-tool.xyz/).

This folder is **self-contained**: it describes everything an AMT-compliant
implementation needs to do, independent of the reference Python implementation.
Anyone can take these files and build a reasoner in Java, Rust, JavaScript or
SPARQL — the ontology specifies the contract.

## Files

| File | Purpose |
|------|---------|
| `amt.ttl` | Classes, properties, logic operators, reasoning rules. |
| `amt-shapes.ttl` | SHACL shapes for validating AMT data files. |
| `examples/` | Small valid and invalid example files used in tests. |
| `../validate_examples.py` | Standalone validation demo (see below). |

## Quick start: run the validation demo

The fastest way to see the ontology and shapes in action is the
`validate_examples.py` script in the project root. It validates both example
files and reports the outcome.

### Folder layout it expects

```
your-project/
├── validate_examples.py
└── ontology/
    ├── amt.ttl
    ├── amt-shapes.ttl
    └── examples/
        ├── example-valid.ttl
        └── example-invalid.ttl
```

### Steps (Windows / VS Code)

1. Open a terminal in VS Code (`Ctrl+ö` or **Terminal → New Terminal**).
2. Install the dependencies once:
   ```
   pip install rdflib pyshacl
   ```
3. Run the script:
   ```
   python validate_examples.py
   ```
   Or just press **F5** / the green Run button in VS Code.

### Expected output

```
AMT Ontology Validation Demo
------------------------------------------------------------------------
========================================================================
  Validating example-valid.ttl  (expected: VALID)
========================================================================
  Result: CONFORMS (no violations found)
  >> Test result: OK   (expected VALID, got VALID)

========================================================================
  Validating example-invalid.ttl  (expected: INVALID)
========================================================================
  Result: NOT CONFORMS - 4 violation(s) found
  [1] ...   amt:weight must be in [0, 1]
  [2] ...   InverseAxiom must have exactly one amt:inverse
  [3] ...   Hamacher requires amt:logicParameter
  [4] ...   Cannot mix legacy and modern antecedents
  >> Test result: OK   (expected INVALID, got INVALID)

========================================================================
  Summary: ALL TESTS PASSED
========================================================================
```

The exit code is `0` when both tests behave as expected, `1` otherwise — so
you can use the script in CI pipelines too.

## Versioning

The ontology is versioned as **Leonard Edition (extended)**. The "extended"
suffix indicates this version adds:

- formal property declarations (domain, range, labels)
- `amt:antecedents` for n-ary role chains (legacy `antecedent1/2` still works)
- additional fuzzy logic operators: Einstein, Geometric Mean, Hamacher
- machine-readable reasoning rule annotations
- SHACL shapes for validation

The original Leonard Edition class hierarchy is preserved unchanged for
backward compatibility.

## What's modelled where

### Class hierarchy (RDFS)

```
amt:Concept     ⊂ rdfs:Class
amt:Role        ⊂ rdf:Property
amt:Axiom       ⊂ rdfs:Class
  ├─ amt:InferenceAxiom
  │    ├─ amt:RoleChainAxiom
  │    └─ amt:InverseAxiom
  └─ amt:IntegrityAxiom
       ├─ amt:DisjointAxiom
       └─ amt:SelfDisjointAxiom
amt:Logic       ⊂ rdfs:Class
amt:ReasoningRule ⊂ rdfs:Class
```

### Logic operators (instances of `amt:Logic`)

| Operator | Arity | Formula | Recommended for |
|----------|-------|---------|-----------------|
| `amt:GoedelLogic` | binary | `min(x, y)` | curated mappings, n=2..3 |
| `amt:ProductLogic` | binary | `x * y` | independent evidence, n=2 |
| `amt:LukasiewiczLogic` | binary | `max(x + y - 1, 0)` | strict reasoning, n=2 only |
| `amt:EinsteinProduct` | binary | `(x*y) / (2 - (x+y - x*y))` | medium-confidence, n=3..4 |
| `amt:GeometricMean` | n-ary | `(x_1 * ... * x_n)^(1/n)` | comparing chains, n≥4 |
| `amt:HamacherProduct` | binary | `(x*y) / (γ + (1-γ)(x+y - x*y))` | tunable, research |

Each operator carries `amt:formula`, `amt:arity`, `amt:isParametrised` and
`amt:recommendedFor` annotations directly in `amt.ttl`. See there for full
descriptions.

### Reasoning rules (instances of `amt:ReasoningRule`)

The four rules a compliant reasoner must implement are documented in
`amt.ttl` with `amt:precondition` and `amt:effect` strings:

- `amt:RoleChainRule` — derives consequent edges from antecedent chains
- `amt:InverseRule` — derives reverse edges from inverse axioms
- `amt:DisjointRule` — flags edges violating disjointness
- `amt:SelfDisjointRule` — flags self-loops on irreflexive roles

These descriptions are normative but informal — RDFS cannot express the
arithmetic of weight propagation. They serve as the spec for any
reimplementation.

## Validation in your own code

If you want to integrate validation into your own pipeline (rather than using
`validate_examples.py` as a demo), here are the building blocks. AMT data
files should be validated against `amt-shapes.ttl` **before** being loaded
into a reasoner — this catches malformed axioms, missing properties,
out-of-range weights and ambiguous notation early.

### Python (pyshacl)

```python
from pyshacl import validate

ok, report_graph, report_text = validate(
    data_graph='my-data.ttl',
    shacl_graph='ontology/amt-shapes.ttl',
    ont_graph='ontology/amt.ttl',
    inference='rdfs',
    advanced=True,  # required for sh:sparql constraints (Hamacher check)
)

if not ok:
    print(report_text)
```

### Other languages

Any SHACL-compliant validator works. For Java use
[TopBraid SHACL](https://github.com/TopQuadrant/shacl), for command-line use
[`pyshacl` CLI](https://github.com/RDFLib/pySHACL) or
[Apache Jena's `shacl` tool](https://jena.apache.org/documentation/shacl/).

### What the shapes check

| Shape | Validates |
|-------|-----------|
| `amt:ConceptShape` | every Concept has at least one `rdfs:label` |
| `amt:RoleShape` | every Role has label, exactly one domain and one range |
| `amt:RoleChainAxiomShape` | exactly one consequent + logic; either `antecedents` (n-ary) **xor** `antecedent1`+`antecedent2` (legacy) |
| `amt:HamacherParameterShape` | axioms using Hamacher must specify `amt:logicParameter` |
| `amt:InverseAxiomShape` | exactly one antecedent and one inverse |
| `amt:DisjointAxiomShape` | exactly one `role1` and one `role2` |
| `amt:SelfDisjointAxiomShape` | exactly one `role` |
| `amt:WeightShape` | `amt:weight` is xsd:decimal in [0, 1] |

## Implementing AMT in another language

If you want to build an AMT-compliant tool, here's the contract:

**1. Data model (from `amt.ttl`)**

Parse Turtle/RDF input. Recognise instances of `amt:Concept`, `amt:Role`,
the four `amt:Axiom` subclasses, `amt:Logic` operators, and weighted
quadruples (RDF reification with `amt:weight`).

**2. Validation (from `amt-shapes.ttl`)**

Run SHACL validation before reasoning. If violations are found, refuse to
proceed or report them clearly.

**3. Reasoning (from `amt:ReasoningRule` instances)**

Implement the role-chain and inverse inference rules. Iterate to a fixed
point: keep applying rules until no new edges are produced. Mark inferred
edges so they can be distinguished from asserted ones.

**4. Logic operators (from `amt:Logic` instances)**

Implement at minimum Gödel, Product and Łukasiewicz (the original three).
For n-ary chains, also implement Einstein, Geometric Mean and optionally
Hamacher.

**Important difference between binary and n-ary operators:** binary
operators (Gödel, Product, Łukasiewicz, Einstein, Hamacher) are
associative and can be applied pairwise:

```
score = w_1
for i in 2..n:
    score = op(score, w_i)
```

N-ary operators (Geometric Mean) must receive the full weight list at once
and cannot be folded pairwise:

```
score = nary_op([w_1, w_2, ..., w_n])
```

The `amt:arity` annotation on each `amt:Logic` instance tells you which
strategy to use.

**5. Consistency checking**

After reasoning, check disjoint and self-disjoint axioms against the
expanded edge set. Report violations but do not modify the graph.

## Compatibility note: legacy vs modern axiom syntax

The original AMT vocabulary uses `amt:antecedent1` and `amt:antecedent2` for
2-step role chains. The extended vocabulary adds `amt:antecedents` (an RDF
list) for chains of arbitrary length. Both forms are valid:

```turtle
# Legacy (still supported)
ex:RCA1 a amt:RoleChainAxiom ;
    amt:antecedent1 ex:knows ;
    amt:antecedent2 ex:knows ;
    amt:consequent  ex:knows ;
    amt:logic       amt:GoedelLogic .

# Modern
ex:RCA2 a amt:RoleChainAxiom ;
    amt:antecedents ( ex:knows ex:knows ) ;
    amt:consequent  ex:knows ;
    amt:logic       amt:GoedelLogic .
```

A compliant parser should accept both. Mixing them on the same axiom is a
SHACL violation.