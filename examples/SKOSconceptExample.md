# SKOS concept matching example — composing the SKOS match properties

This example demonstrates AMT.engine reasoning over SKOS-style concept
mappings. Four concepts are linked by `skos:exactMatch`,
`skos:closeMatch` and `skos:relatedMatch`, plus a project-internal
`skosplus:MatchStar7` role used to show how to introduce a custom
typed-mapping relation alongside the standard SKOS vocabulary.

The interesting question this example answers: **what should happen
when you compose two SKOS match properties?** Eight role-chain axioms
spell out the engine's behaviour for every binary composition that
matters in practice, picking a logic operator for each one based on
what the composition actually means.

Run it with:

```bash
python -m amt.runner examples/SKOSconceptExample.ttl
```

## The match graph

Four concepts, four asserted edges:

```mermaid
---
config:
  layout: elk
  theme: neutral
---
flowchart LR
    C1["Concept1"]
    C2["Concept2"]
    C3["Concept3"]
    C4["Concept4"]

    C1 -->|"exactMatch 1.00"|   C2
    C1 -->|"closeMatch 0.94"|   C2
    C2 -->|"closeMatch 0.94"|   C4
    C2 -->|"relatedMatch 0.49"| C3
```

Concept1 and Concept2 are doubly linked — once as exact identity (1.0)
and once as close mapping (0.94). This redundancy is intentional: it
gives the engine multiple paths to derive the same edge, exercising
the reasoner's max-aggregation and provenance-merging behaviour.

## Why two ways from Concept1 to Concept2?

Asserting both `exactMatch` (1.0) and `closeMatch` (0.94) for the same
pair is unusual but legitimate — it would happen, for example, if two
different mapping projects produced different verdicts on the same
concept pair and you wanted to keep both pieces of evidence in the
graph rather than merging them upstream. The reasoner doesn't require
you to deduplicate: it processes both edges independently and records
which axioms used which input.

## Axioms used

Eight `RoleChainAxiom`s. Three logic operators (Goedel, Product,
Łukasiewicz) cover every meaningful binary composition. A custom
`questionableMatch` role is used as the consequent for chains whose
results should be flagged for human review.

| Axiom | Logic | Why this logic |
|-------|-------|----------------|
| `RCA_exactTransitive`<br>`exactMatch ∘ exactMatch → exactMatch` | **Goedel** | Transitive identity. The composed match is no stronger than its weakest link — there's no "stacking of evidence" reading that would justify multiplication. |
| `RCA_closeTransitive`<br>`closeMatch ∘ closeMatch → closeMatch` | **Product** | closeMatch is fuzzy equivalence. Two independent fuzzy mappings combine multiplicatively. |
| `RCA_relatedQuestionable`<br>`relatedMatch ∘ relatedMatch → questionableMatch` | **Łukasiewicz** | relatedMatch is already weak. Composing two of them should produce something even weaker, and only fire if both inputs clear a high threshold (max(0, x+y-1)). The result is `questionableMatch` because chains of related-links are exactly what humans should review. |
| `RCA_matchStar7Trans`<br>`MatchStar7 ∘ MatchStar7 → MatchStar7` | **Goedel** | Project-internal classification-like relation. Same reasoning as exactMatch: weakest-link composition. |
| `RCA_exactClose`<br>`exactMatch ∘ closeMatch → closeMatch` | **Product** | Exact identity followed by close mapping yields close. Product because the close link is the limiting factor. |
| `RCA_closeExact`<br>`closeMatch ∘ exactMatch → closeMatch` | **Product** | Symmetric counterpart of the above. Needed explicitly because role-chain composition is not commutative in SKOS. |
| `RCA_exactRelated`<br>`exactMatch ∘ relatedMatch → closeMatch` | **Product** | Identity followed by a weak related-link. Result is close-not-exact, with the relatedMatch dampening confidence. |
| `RCA_closeRelated`<br>`closeMatch ∘ relatedMatch → closeMatch` | **Product** | Same shape as exactRelated, with the leading edge being close instead of exact. |

A subtle modelling choice: **the relatedMatch chain produces
`questionableMatch`, not `relatedMatch`**. This is what makes
relatedMatch chains visible in the output and reviewable. If you
wanted standard SKOS-only consequents, you'd change the axiom's
consequent to `skos:relatedMatch` and lose the flag-for-review signal.

## Expected inferences

After running the pipeline you should see **2 inferred edges**, each
derived by two different axioms.

### Inferred edge 1: `Concept1 → Concept4` as closeMatch

Two derivations both reach this edge:

| Path | Logic | Weight |
|------|-------|--------|
| `Concept1 -exact-> Concept2 -close-> Concept4` | Product (RCA_exactClose) | 1.00 × 0.94 = **0.940** |
| `Concept1 -close-> Concept2 -close-> Concept4` | Product (RCA_closeTransitive) | 0.94 × 0.94 = 0.884 |

The reasoner takes the **maximum** (0.940) as the final weight and
merges both axiom IRIs into the edge's provenance. In the output
this looks like:

```turtle
_:i1 rdf:subject     ex:Concept1 ;
     rdf:predicate   skos:closeMatch ;
     rdf:object      ex:Concept4 ;
     amt:weight      "0.940000"^^xsd:double ;
     amt:inferred    "true"^^xsd:boolean ;
     amt:provenance  ex:RCA_closeTransitive, ex:RCA_exactClose .
```

### Inferred edge 2: `Concept1 → Concept3` as closeMatch

Same pattern — two derivations:

| Path | Logic | Weight |
|------|-------|--------|
| `Concept1 -exact-> Concept2 -related-> Concept3` | Product (RCA_exactRelated) | 1.00 × 0.49 = **0.490** |
| `Concept1 -close-> Concept2 -related-> Concept3` | Product (RCA_closeRelated) | 0.94 × 0.49 = 0.461 |

Final: weight 0.490, provenance `[RCA_exactRelated, RCA_closeRelated]`.

## Axioms that don't fire on this dataset

Four of the eight axioms produce no inferences here:

- **`RCA_exactTransitive`** — only one `exactMatch` edge in the data;
  needs a chain of two.
- **`RCA_relatedQuestionable`** — only one `relatedMatch` edge in the
  data.
- **`RCA_matchStar7Trans`** — no `MatchStar7` edges asserted.
- **`RCA_closeExact`** — no `closeMatch ∘ exactMatch` chain (would
  need a closeMatch edge ending at Concept2 followed by an
  exactMatch from Concept2; we have it the other way around).

Including axioms that don't fire on the bundled data is intentional.
A real SKOS dataset has thousands of edges, and the engine should be
configured for the full vocabulary, not just the subset that happens
to appear in a four-concept example.

## A modelling caveat: derived `closeMatch` from `exactMatch ∘ relatedMatch`

The inference `Concept1 closeMatch Concept3` (weight 0.49) deserves
scrutiny. Concept1 and Concept2 are exactly identical (1.0); Concept2
and Concept3 are only weakly related (0.49). Should we then claim
that Concept1 and Concept3 are "close"?

Two readings:

1. **Yes, with low confidence.** "Close" doesn't mean "very close" —
   it means "in the close-mapping equivalence class". A weight of
   0.49 honestly reflects "we believe this with about 50%
   confidence", which is a usable signal in downstream reasoning.
2. **No, this should be relatedMatch.** Identity composed with
   related-of-X should yield related-of-X, not close-of-X. Under
   this view, the axiom should have `consequent skos:relatedMatch`
   instead of `closeMatch`.

The example uses reading (1) because it makes the SKOS hierarchy
flow upward (relatedMatch < closeMatch < exactMatch) more visible
in the output. If you'd prefer reading (2), changing the four
mixed-strength axioms (`RCA_exactRelated`, `RCA_closeRelated`,
`RCA_exactClose`, `RCA_closeExact`) is a one-line edit per axiom.

## Suggested extensions

To exercise more of the axioms, add data:

```turtle
# Trigger RCA_exactTransitive — produces Concept1 exactMatch Concept5
# at min(1.0, 1.0) = 1.0
ex:Concept5 amt:instanceOf ex:Concept ; rdfs:label "Concept 5" .
_:n05 rdf:subject ex:Concept2 ; rdf:predicate skos:exactMatch ;
      rdf:object ex:Concept5 ; amt:weight "1.00"^^xsd:decimal .

# Trigger RCA_relatedQuestionable — produces Concept2 questionableMatch X
# at max(0, 0.49 + w - 1)
_:n06 rdf:subject ex:Concept3 ; rdf:predicate skos:relatedMatch ;
      rdf:object ex:Concept5 ; amt:weight "0.80"^^xsd:decimal .
# → Concept2 questionableMatch Concept5 at max(0, 0.49 + 0.80 - 1) = 0.29

# Trigger RCA_matchStar7Trans — needs two MatchStar7 edges in a chain
_:n07 rdf:subject ex:Concept1 ; rdf:predicate skosplus:MatchStar7 ;
      rdf:object ex:Concept5 ; amt:weight "0.85"^^xsd:decimal .
_:n08 rdf:subject ex:Concept5 ; rdf:predicate skosplus:MatchStar7 ;
      rdf:object ex:Concept4 ; amt:weight "0.90"^^xsd:decimal .
# → Concept1 MatchStar7 Concept4 at min(0.85, 0.90) = 0.85
```

These extensions are not in the bundled file because the example
deliberately keeps the dataset minimal — every asserted edge serves
to illustrate a specific reasoning behaviour, and adding more would
make the inference table harder to read at a glance. For a richer
dataset that exercises all six logic operators including the n-ary
ones, see the bundled `examples/skos-mapping-example.ttl`.
