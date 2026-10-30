"""
Tests for type and method on statements (the hextuple, PRIMER S21).

A statement is (subject, role, object, weight); the FW ontology adds
``fw:hasType`` and ``fw:hasMethod``. The rules tested here are the ones in
PRIMER A4 of 2026-10-30: both weight properties are read, a statement without
a type is a vagueness statement, derived statements get method and type from
their axiom, and the output can be read again without loss.
"""
from __future__ import annotations

import csv
from pathlib import Path

import pytest

from amt import do_reasoning, load_amt
from amt.diagnostics import diagnose
from amt.export import export_csv, export_cypher, export_ttl
from amt.fw import (
    DEFAULT_TYPE, FUZZINESS_WOBBLINESS, UNCERTAINTY, VAGUENESS,
    combine_types, effective_type, stored_type,
)
from amt.validation import validate_against_shapes

ROOT = Path(__file__).resolve().parent.parent
DEMO = ROOT / "examples" / "hextuple-demo.ttl"
FW = "http://w3id.org/fw_ontology/"
AMT = "http://academic-meta-tool.xyz/vocab#"

PREFIXES = f"""@prefix amt: <{AMT}> .
@prefix fw: <{FW}> .
@prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .
@prefix rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#> .
@prefix ex: <http://example.org/> .
ex:C a amt:Concept ; rdfs:label "C" .
ex:a amt:instanceOf ex:C ; rdfs:label "a" .
ex:b amt:instanceOf ex:C ; rdfs:label "b" .
"""


def _short(e):
    n = lambda x: x.rsplit("/", 1)[-1].rsplit("#", 1)[-1] if x else None
    return (n(e["from"]), n(e["role"]), n(e["to"]), round(e["weight"], 6), n(e["type"]), n(e["method"]))


def _export(amt, **kw):
    return export_ttl(amt["nodes"], amt["edges"], amt["concepts"], amt["roles"], amt["axioms"],
                      amt["graph"], amt["prefix"], **kw)


# ── helpers ────────────────────────────────────────────────────────────────
def test_the_default_type_is_vagueness():
    assert DEFAULT_TYPE == VAGUENESS == FW + "Vagueness"
    assert effective_type({"type": None}) == VAGUENESS
    assert effective_type({}) == VAGUENESS
    assert effective_type({"type": UNCERTAINTY}) == UNCERTAINTY
    assert stored_type(VAGUENESS) is None and stored_type(UNCERTAINTY) == UNCERTAINTY


def test_combine_types():
    assert combine_types([None, None]) == VAGUENESS
    assert combine_types([None, VAGUENESS]) == VAGUENESS            # a missing type is vagueness
    assert combine_types([UNCERTAINTY, UNCERTAINTY]) == UNCERTAINTY
    assert combine_types([UNCERTAINTY, None]) == FUZZINESS_WOBBLINESS
    assert combine_types([UNCERTAINTY, VAGUENESS, UNCERTAINTY]) == FUZZINESS_WOBBLINESS
    assert combine_types([FUZZINESS_WOBBLINESS, FUZZINESS_WOBBLINESS]) == FUZZINESS_WOBBLINESS


# ── loading ────────────────────────────────────────────────────────────────
def test_loader_reads_type_method_evidence_and_both_weight_properties():
    amt = load_amt(DEMO)
    by = {_short(e)[:3]: e for e in amt["edges"]}
    attributed = by[("c1", "attributedTo", "vespasian")]
    assert attributed["type"] == UNCERTAINTY and attributed["method"] == FW + "EqualShareRule"
    assert attributed["evidence"][0]["id"] is None
    assert any(o.endswith("Obverse legend damaged: IMP CAES VESP or TITVS.\"") for _, o in attributed["evidence"][0]["properties"])
    assert by[("c1", "attributedTo", "titus")]["evidence"] is None
    assert by[("c1", "struckAt", "rome")]["weight"] == pytest.approx(0.9)       # fw:hasDegreeOfConnection
    assert by[("c1", "struckAt", "rome")]["type"] is None                        # default stays implicit
    assert by[("c2", "struckAt", "lugdunum")]["type"] == VAGUENESS               # explicit stays explicit


def test_a_quadruple_loads_with_empty_hextuple_keys():
    amt = load_amt(ROOT / "examples" / "animals.ttl")
    assert all(e["type"] is None and e["method"] is None and e["evidence"] is None for e in amt["edges"])


def test_amt_weight_wins_over_the_fw_name_and_the_conflict_is_reported():
    ttl = PREFIXES + "[] rdf:subject ex:a ; rdf:predicate ex:r ; rdf:object ex:b ; amt:weight 0.4 ; fw:hasDegreeOfConnection 0.9 .\n"
    amt = load_amt(ttl)
    assert [e["weight"] for e in amt["edges"]] == [0.4]
    assert [f.code for f in diagnose(amt)].count("AMT-E104") == 1
    same = PREFIXES + "[] rdf:subject ex:a ; rdf:predicate ex:r ; rdf:object ex:b ; amt:weight 0.4 ; fw:hasDegreeOfConnection 0.4 .\n"
    assert "AMT-E104" not in [f.code for f in diagnose(load_amt(same))]


# ── reasoning ──────────────────────────────────────────────────────────────
def test_derived_edges_get_method_and_type_from_the_axiom():
    amt = load_amt(DEMO)
    got = {_short(e) for e in do_reasoning(amt["edges"], amt["axioms"]) if e["inferred"]}
    assert got == {
        ("c1", "struckIn", "latium", 0.9, None, "GoedelLogic"),                       # all vague: default, implicit
        ("c2", "struckIn", "gaul", 0.7, "FuzzinessWobbliness", "GoedelLogic"),        # vagueness + uncertainty
        ("c1", "linkedTo", "latium", 0.4, "FuzzinessWobbliness", "ProductLogic"),
        ("latium", "producedCoin", "c1", 0.9, None, None),                            # inverse: no method, type of source
        ("gaul", "producedCoin", "c2", 0.7, "FuzzinessWobbliness", None),
    }


def test_same_type_on_all_antecedents_is_kept():
    ttl = PREFIXES + """
ex:r1 a amt:Role ; rdfs:label "r1" ; rdfs:domain ex:C ; rdfs:range ex:C .
ex:r2 a amt:Role ; rdfs:label "r2" ; rdfs:domain ex:C ; rdfs:range ex:C .
ex:r3 a amt:Role ; rdfs:label "r3" ; rdfs:domain ex:C ; rdfs:range ex:C .
ex:c amt:instanceOf ex:C ; rdfs:label "c" .
ex:ax a amt:RoleChainAxiom ; amt:antecedents ( ex:r1 ex:r2 ) ; amt:consequent ex:r3 ; amt:logic amt:GoedelLogic .
[] rdf:subject ex:a ; rdf:predicate ex:r1 ; rdf:object ex:b ; amt:weight 0.5 ; fw:hasType fw:Uncertainty .
[] rdf:subject ex:b ; rdf:predicate ex:r2 ; rdf:object ex:c ; amt:weight 0.6 ; fw:hasType fw:Uncertainty .
"""
    amt = load_amt(ttl)
    derived = [e for e in do_reasoning(amt["edges"], amt["axioms"]) if e["inferred"]]
    assert [(e["type"], e["method"]) for e in derived] == [(UNCERTAINTY, AMT + "GoedelLogic")]


def test_several_paths_the_highest_weight_decides_and_a_tie_the_smallest_method():
    ttl = PREFIXES + """
ex:r1 a amt:Role ; rdfs:label "r1" ; rdfs:domain ex:C ; rdfs:range ex:C .
ex:r2 a amt:Role ; rdfs:label "r2" ; rdfs:domain ex:C ; rdfs:range ex:C .
ex:r3 a amt:Role ; rdfs:label "r3" ; rdfs:domain ex:C ; rdfs:range ex:C .
ex:axG a amt:RoleChainAxiom ; amt:antecedents ( ex:r1 ex:r2 ) ; amt:consequent ex:r3 ; amt:logic amt:GoedelLogic .
ex:axP a amt:RoleChainAxiom ; amt:antecedents ( ex:r1 ex:r2 ) ; amt:consequent ex:r3 ; amt:logic amt:ProductLogic .
[] rdf:subject ex:a ; rdf:predicate ex:r1 ; rdf:object ex:b ; amt:weight 1.0 .
[] rdf:subject ex:b ; rdf:predicate ex:r2 ; rdf:object ex:b ; amt:weight 0.5 .
"""
    amt = load_amt(ttl)
    # Goedel gives min(1, .5) = .5, Product 1 * .5 = .5: equal weight, the smaller method IRI wins.
    results = []
    for axioms in (amt["axioms"], list(reversed(amt["axioms"]))):
        derived = [e for e in do_reasoning(amt["edges"], axioms) if e["inferred"] and e["role"].endswith("r3")]
        assert len(derived) == 1
        results.append((derived[0]["weight"], derived[0]["method"]))
    assert results[0] == results[1] == (0.5, AMT + "GoedelLogic")


def test_higher_weight_path_replaces_type_and_method():
    ttl = PREFIXES + """
ex:r1 a amt:Role ; rdfs:label "r1" ; rdfs:domain ex:C ; rdfs:range ex:C .
ex:r2 a amt:Role ; rdfs:label "r2" ; rdfs:domain ex:C ; rdfs:range ex:C .
ex:r3 a amt:Role ; rdfs:label "r3" ; rdfs:domain ex:C ; rdfs:range ex:C .
ex:axG a amt:RoleChainAxiom ; amt:antecedents ( ex:r1 ex:r2 ) ; amt:consequent ex:r3 ; amt:logic amt:GoedelLogic .
ex:axL a amt:RoleChainAxiom ; amt:antecedents ( ex:r1 ex:r2 ) ; amt:consequent ex:r3 ; amt:logic amt:LukasiewiczLogic .
[] rdf:subject ex:a ; rdf:predicate ex:r1 ; rdf:object ex:b ; amt:weight 0.9 ; fw:hasType fw:Uncertainty .
[] rdf:subject ex:b ; rdf:predicate ex:r2 ; rdf:object ex:b ; amt:weight 0.8 ; fw:hasType fw:Uncertainty .
"""
    amt = load_amt(ttl)
    derived = [e for e in do_reasoning(amt["edges"], amt["axioms"]) if e["inferred"]]
    assert len(derived) == 1
    # Goedel .8 beats Lukasiewicz .7
    assert (derived[0]["weight"], derived[0]["method"]) == (pytest.approx(0.8), AMT + "GoedelLogic")


def test_asserted_edges_keep_their_type_and_method_when_an_axiom_also_supports_them():
    amt = load_amt(DEMO)
    asserted = [e for e in amt["edges"]]
    reasoned = do_reasoning(asserted, amt["axioms"])
    for before, after in zip(asserted, reasoned):
        assert (before["type"], before["method"]) == (after["type"], after["method"])
    assert asserted[0] is not reasoned[0]        # the input is not mutated
    assert all(e["type"] in (None, UNCERTAINTY, VAGUENESS) for e in asserted)


# ── export and roundtrip ───────────────────────────────────────────────────
def test_turtle_roundtrip_keeps_weight_type_method_and_evidence():
    amt = load_amt(DEMO)
    reasoned = do_reasoning(amt["edges"], amt["axioms"])
    ttl = _export(amt, with_reasoning=True, reasoned_edges=reasoned)
    again = load_amt(ttl)
    assert sorted(_short(e) for e in again["edges"]) == sorted(_short(e) for e in reasoned)
    ev = lambda edges: sorted(str(e["evidence"]) for e in edges if e["evidence"])
    assert ev(again["edges"]) == ev(reasoned) and len(ev(reasoned)) == 1


def test_the_output_validates_and_the_default_type_is_not_written():
    amt = load_amt(DEMO)
    ttl = _export(amt, with_reasoning=True)
    assert validate_against_shapes(ttl).conforms
    # Written: four typed input statements (one of them the explicit default)
    # and the three derived edges that are not vague; c1 struckIn latium is.
    assert ttl.count("fw:hasType") == 4 + 3
    assert "fw:Vagueness" in ttl                       # the explicit one stays
    animals = load_amt(ROOT / "examples" / "animals.ttl")
    asserted_only = _export(animals)
    assert "fw:" not in asserted_only                  # a quadruple stays a quadruple
    reasoned = _export(animals, with_reasoning=True)
    assert "fw:hasType" not in reasoned                # every derived edge is vague: the default is not written
    assert "fw:hasMethod" in reasoned                  # but each says which logic produced it
    assert '"1.000000"^^xsd:decimal' in reasoned and "xsd:double" not in reasoned


@pytest.mark.parametrize("name", ["animals.ttl", "subsumption-demo.ttl", "SKOSconceptExample.ttl", "hextuple-demo.ttl"])
def test_reasoned_output_of_every_example_passes_the_shapes(name):
    amt = load_amt(ROOT / "examples" / name)
    result = validate_against_shapes(_export(amt, with_reasoning=True))
    assert result.conforms, result.report_text[:600]


def test_runner_output_reads_back_for_the_demo(tmp_path):
    from amt.runner import run_all
    run_all(DEMO, output_dir=tmp_path, info=False)
    reasoned = load_amt(tmp_path / "hextuple-demo.reasoned.ttl")
    original = load_amt(DEMO)
    want = do_reasoning(original["edges"], original["axioms"])
    assert sorted(_short(e) for e in reasoned["edges"]) == sorted(_short(e) for e in want)


def test_csv_has_the_new_columns_last_and_shows_the_effective_type(tmp_path):
    amt = load_amt(DEMO)
    _, edges_path = export_csv(amt["nodes"], amt["edges"], amt["axioms"], tmp_path, with_reasoning=True)
    rows = list(csv.reader(edges_path.open(encoding="utf-8")))
    assert rows[0] == ["source_iri", "target_iri", "role_iri", "weight", "inferred", "provenance", "type", "method"]
    by = {(r[0].rsplit("/", 1)[-1], r[2].rsplit("/", 1)[-1], r[1].rsplit("/", 1)[-1]): r for r in rows[1:]}
    assert by[("c1", "struckAt", "rome")][6] == VAGUENESS and by[("c1", "struckAt", "rome")][7] == ""
    assert by[("c1", "struckIn", "latium")][6:] == [VAGUENESS, AMT + "GoedelLogic"]
    assert by[("c1", "linkedTo", "latium")][6] == FUZZINESS_WOBBLINESS


def test_cypher_carries_type_and_method():
    amt = load_amt(DEMO)
    text = export_cypher(amt["nodes"], amt["edges"], amt["axioms"], with_reasoning=True)
    assert 'type: "FuzzinessWobbliness", method: "ProductLogic"' in text
    assert 'type: "Vagueness"}' in text


# ── diagnostics ────────────────────────────────────────────────────────────
def test_unknown_type_is_a_warning_and_kept():
    ttl = PREFIXES + "[] rdf:subject ex:a ; rdf:predicate ex:r ; rdf:object ex:b ; amt:weight 0.4 ; fw:hasType ex:Maybe .\n"
    amt = load_amt(ttl)
    codes = [f.code for f in diagnose(amt)]
    assert "AMT-W205" in codes
    assert amt["edges"][0]["type"] == "http://example.org/Maybe"


def test_type_without_method_is_a_note_and_a_method_without_type_is_not():
    typed = PREFIXES + "[] rdf:subject ex:a ; rdf:predicate ex:r ; rdf:object ex:b ; amt:weight 0.4 ; fw:hasType fw:Uncertainty .\n"
    meth = PREFIXES + "[] rdf:subject ex:a ; rdf:predicate ex:r ; rdf:object ex:b ; amt:weight 0.4 ; fw:hasMethod fw:EqualShareRule .\n"
    assert "AMT-N303" in [f.code for f in diagnose(load_amt(typed))]
    assert "AMT-N303" not in [f.code for f in diagnose(load_amt(meth))]


def test_the_demo_has_no_error_or_warning():
    levels = {f.level for f in diagnose(load_amt(DEMO))}
    assert levels <= {"note"}


def test_the_six_logics_are_propagation_methods():
    from rdflib import Graph, RDF, URIRef
    g = Graph().parse(ROOT / "ontology" / "amt.ttl", format="turtle")
    logics = set(g.subjects(RDF.type, URIRef(AMT + "Logic")))
    methods = set(g.subjects(RDF.type, URIRef(FW + "PropagationMethod")))
    assert len(logics) == 6 and logics <= methods
