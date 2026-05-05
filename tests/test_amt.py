"""
Smoke tests for the AMT package. Exercise each module against the bundled
example files plus a few synthetic cases for the new n-ary functionality.
"""
from __future__ import annotations

import math
from pathlib import Path

import pytest

from amt import (
    AMTValidationError,
    aggregate_weights,
    check_consistency,
    do_reasoning,
    export_csv,
    export_cypher,
    export_ttl,
    load_amt,
    validate_against_shapes,
    GOEDEL, PRODUCT, LUKASIEWICZ, EINSTEIN, GEOMETRIC, HAMACHER,
)

ROOT = Path(__file__).resolve().parent.parent
EXAMPLES = ROOT / "examples"
ONTOLOGY_EX = ROOT / "ontology" / "examples"


# ─────────────────────────────────────────────────────────────────────────
# Logic tests
# ─────────────────────────────────────────────────────────────────────────
class TestLogic:
    def test_goedel_is_min(self):
        assert aggregate_weights([0.8, 0.6, 0.5], GOEDEL) == 0.5

    def test_product(self):
        assert aggregate_weights([0.8, 0.6, 0.5], PRODUCT) == 0.24

    def test_lukasiewicz_clamps_to_zero(self):
        # 0.8 + 0.6 + 0.5 - 2 = -0.1 -> max(., 0) = 0
        assert aggregate_weights([0.8, 0.6, 0.5], LUKASIEWICZ) == 0.0

    def test_lukasiewicz_with_high_weights(self):
        # 0.9 + 0.9 - 1 = 0.8
        assert aggregate_weights([0.9, 0.9], LUKASIEWICZ) == 0.8

    def test_einstein_associative_pairwise(self):
        # Einstein folds pairwise; verify a known triple
        v = aggregate_weights([0.8, 0.6, 0.5], EINSTEIN)
        # left-fold: einstein(einstein(0.8, 0.6), 0.5)
        # einstein(0.8, 0.6) = 0.48 / (2 - 1.4 + 0.48) = 0.48/1.08 ~ 0.4444
        # einstein(0.4444, 0.5) ~ 0.2222 / (2 - 0.9444 + 0.2222) ~ 0.1739
        assert abs(v - 0.173913) < 1e-5

    def test_geometric_mean_is_nth_root(self):
        v = aggregate_weights([0.8, 0.6, 0.5], GEOMETRIC)
        expected = (0.8 * 0.6 * 0.5) ** (1.0 / 3.0)
        assert abs(v - expected) < 1e-5

    def test_hamacher_requires_parameter(self):
        with pytest.raises(ValueError, match="logicParameter"):
            aggregate_weights([0.5, 0.5], HAMACHER)

    def test_hamacher_with_gamma_one_equals_product(self):
        # Hamacher with gamma=1 is the algebraic product.
        v_h = aggregate_weights([0.6, 0.7], HAMACHER, parameter=1.0)
        v_p = aggregate_weights([0.6, 0.7], PRODUCT)
        assert abs(v_h - v_p) < 1e-6

    def test_unknown_logic_raises(self):
        with pytest.raises(ValueError, match="Unknown logic"):
            aggregate_weights([0.5], "http://nope.example.com/Foo")

    def test_empty_list_raises(self):
        with pytest.raises(ValueError, match="empty"):
            aggregate_weights([], GOEDEL)

    def test_single_element(self):
        # All operators reduce to identity for n=1
        for logic in (GOEDEL, PRODUCT, LUKASIEWICZ, EINSTEIN, GEOMETRIC):
            assert aggregate_weights([0.7], logic) == 0.7


# ─────────────────────────────────────────────────────────────────────────
# Validation tests
# ─────────────────────────────────────────────────────────────────────────
class TestValidation:
    def test_valid_example_passes(self):
        result = validate_against_shapes(ONTOLOGY_EX / "example-valid.ttl")
        assert result.conforms
        assert result.violations == []

    def test_invalid_example_fails_with_four_violations(self):
        result = validate_against_shapes(ONTOLOGY_EX / "example-invalid.ttl")
        assert not result.conforms
        assert len(result.violations) == 4

    def test_load_amt_with_validate_passes_on_valid(self):
        amt = load_amt(ONTOLOGY_EX / "example-valid.ttl", validate=True)
        assert len(amt["axioms"]) == 4

    def test_load_amt_with_validate_raises_on_invalid(self):
        with pytest.raises(AMTValidationError):
            load_amt(ONTOLOGY_EX / "example-invalid.ttl", validate=True)


# ─────────────────────────────────────────────────────────────────────────
# Loader tests
# ─────────────────────────────────────────────────────────────────────────
class TestLoader:
    def test_chain_test_loads(self):
        amt = load_amt(EXAMPLES / "chain-test.ttl")
        assert len(amt["concepts"]) == 1
        assert len(amt["roles"]) == 2
        assert len(amt["nodes"]) == 4
        assert len(amt["edges"]) == 3
        assert len(amt["axioms"]) == 2

    def test_legacy_antecedents_normalised_to_list(self):
        amt = load_amt(EXAMPLES / "chain-test.ttl")
        rca2 = next(a for a in amt["axioms"] if a["type"] == "RoleChainAxiom"
                    and "antecedent1" in a)
        # Both legacy keys preserved AND the modern unified list
        assert "antecedent1" in rca2
        assert "antecedent2" in rca2
        assert rca2["antecedents"] == [rca2["antecedent1"], rca2["antecedent2"]]

    def test_modern_antecedents_parsed_as_list(self):
        amt = load_amt(EXAMPLES / "chain-test.ttl")
        rca3 = next(a for a in amt["axioms"] if a["type"] == "RoleChainAxiom"
                    and "antecedent1" not in a)
        assert len(rca3["antecedents"]) == 3

    def test_hamacher_parameter_parsed_as_float(self):
        amt = load_amt(ONTOLOGY_EX / "example-valid.ttl")
        ham = next(a for a in amt["axioms"] if a.get("logic", "").endswith("HamacherProduct"))
        assert isinstance(ham["logicParameter"], float)
        assert ham["logicParameter"] == 2.0

    def test_edges_have_inferred_and_provenance_fields(self):
        amt = load_amt(EXAMPLES / "chain-test.ttl")
        for e in amt["edges"]:
            assert e["inferred"] is False
            assert e["provenance"] == []


# ─────────────────────────────────────────────────────────────────────────
# Reasoning tests
# ─────────────────────────────────────────────────────────────────────────
class TestReasoning:
    @pytest.fixture
    def reasoned(self):
        amt = load_amt(EXAMPLES / "chain-test.ttl")
        return do_reasoning(amt["edges"], amt["axioms"])

    def test_2ary_chain_produces_inferred_edge(self, reasoned):
        # alice --knows--> carol must exist after RCA2 fires
        match = next(
            (e for e in reasoned
             if e["from"].endswith("/alice") and e["to"].endswith("/carol")
             and e["role"].endswith("/knows")),
            None,
        )
        assert match is not None
        assert match["inferred"]
        assert match["weight"] == 0.8  # min(0.9, 0.8)

    def test_3ary_geometric_mean_chain(self, reasoned):
        # alice --trusts--> dave via RCA3, weight = (0.9*0.8*0.7)^(1/3)
        match = next(
            (e for e in reasoned
             if e["from"].endswith("/alice") and e["to"].endswith("/dave")
             and e["role"].endswith("/trusts")),
            None,
        )
        assert match is not None
        assert match["inferred"]
        expected = (0.9 * 0.8 * 0.7) ** (1.0 / 3.0)
        assert abs(match["weight"] - expected) < 1e-5

    def test_provenance_records_axiom_iri(self, reasoned):
        for e in reasoned:
            if e.get("inferred"):
                assert len(e["provenance"]) >= 1
                # Provenance must reference an axiom IRI
                assert all(p.startswith("http") for p in e["provenance"])

    def test_does_not_mutate_input(self):
        amt = load_amt(EXAMPLES / "chain-test.ttl")
        n_before = len(amt["edges"])
        _ = do_reasoning(amt["edges"], amt["axioms"])
        assert len(amt["edges"]) == n_before

    def test_fixed_point_reached(self, reasoned):
        # Running reasoning again on the result should not produce new edges.
        # We synthesise this by re-running reasoning on the reasoned set.
        amt = load_amt(EXAMPLES / "chain-test.ttl")
        once = do_reasoning(amt["edges"], amt["axioms"])
        twice = do_reasoning(once, amt["axioms"])
        # Edge counts should be identical (provenance might grow, but
        # not the number of distinct edges)
        keys_once = {(e["role"], e["from"], e["to"]) for e in once}
        keys_twice = {(e["role"], e["from"], e["to"]) for e in twice}
        assert keys_once == keys_twice


# ─────────────────────────────────────────────────────────────────────────
# Export tests (round-trip)
# ─────────────────────────────────────────────────────────────────────────
class TestExport:
    def test_ttl_roundtrip_preserves_axioms(self, tmp_path):
        amt = load_amt(EXAMPLES / "chain-test.ttl")
        ttl = export_ttl(
            amt["nodes"], amt["edges"], amt["concepts"], amt["roles"],
            amt["axioms"], rdf_graph=amt["graph"], prefix=amt["prefix"],
            with_reasoning=True,
        )
        path = tmp_path / "rt.ttl"
        path.write_text(ttl, encoding="utf-8")
        amt2 = load_amt(path)
        assert len(amt2["axioms"]) == len(amt["axioms"])
        assert len(amt2["concepts"]) == len(amt["concepts"])
        assert len(amt2["nodes"]) == len(amt["nodes"])
        # Reasoned export doubles edge counts (asserted + inferred)
        assert len(amt2["edges"]) > len(amt["edges"])

    def test_ttl_without_vocabulary_is_smaller(self, tmp_path):
        amt = load_amt(EXAMPLES / "chain-test.ttl")
        with_vocab = export_ttl(
            amt["nodes"], amt["edges"], amt["concepts"], amt["roles"],
            amt["axioms"], rdf_graph=amt["graph"], prefix=amt["prefix"],
            include_vocabulary=True,
        )
        without_vocab = export_ttl(
            amt["nodes"], amt["edges"], amt["concepts"], amt["roles"],
            amt["axioms"], rdf_graph=amt["graph"], prefix=amt["prefix"],
            include_vocabulary=False,
        )
        assert len(with_vocab) > len(without_vocab)

    def test_csv_export_writes_two_files(self, tmp_path):
        amt = load_amt(EXAMPLES / "chain-test.ttl")
        n_path, e_path = export_csv(
            amt["nodes"], amt["edges"], amt["axioms"],
            tmp_path, with_reasoning=True,
        )
        assert n_path.exists() and e_path.exists()
        # nodes.csv: header + 4 nodes
        assert len(n_path.read_text().splitlines()) == 5
        # edges.csv: header + 7 edges (3 asserted + 4 inferred)
        assert len(e_path.read_text().splitlines()) == 8

    def test_cypher_export_includes_provenance(self, tmp_path):
        amt = load_amt(EXAMPLES / "chain-test.ttl")
        cy = export_cypher(
            amt["nodes"], amt["edges"], amt["axioms"],
            with_reasoning=True,
        )
        assert "provenance" in cy
        assert "RCA2" in cy or "RCA3" in cy


# ─────────────────────────────────────────────────────────────────────────
# Consistency tests
# ─────────────────────────────────────────────────────────────────────────
class TestConsistency:
    def test_chain_test_is_consistent(self):
        amt = load_amt(EXAMPLES / "chain-test.ttl")
        ok, violations = check_consistency(amt["edges"], amt["axioms"])
        assert ok
        assert violations == []
