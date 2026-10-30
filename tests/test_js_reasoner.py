"""
The JavaScript reasoner (docs/js/amt-reasoner.js) must give the same results as
the Python engine. The browser pages (Explorer, Playground) run that file, so a
difference here would be a difference between what people see and what
``amt-runner`` writes.

Both are run on every bundled example and on a grid of weights for each fuzzy
logic. The tests are skipped when Node.js is not installed.
"""
from __future__ import annotations

import itertools
import json
import shutil
import subprocess
from pathlib import Path

import pytest

from amt import aggregate_weights, check_consistency, do_reasoning, load_amt
from amt.core import AMT_PFX
from amt.reasoning import reason_with_stats

ROOT = Path(__file__).resolve().parent.parent
RUNNER = ROOT / "tests" / "js" / "run_reasoner.js"
EXAMPLES = sorted((ROOT / "examples").glob("*.ttl"))

pytestmark = pytest.mark.skipif(shutil.which("node") is None, reason="Node.js is not installed")


def _node(request: dict):
    done = subprocess.run(
        ["node", str(RUNNER)], input=json.dumps(request), capture_output=True, text=True, check=True, timeout=60
    )
    return json.loads(done.stdout)


def test_the_examples_are_found():
    assert len(EXAMPLES) >= 6


@pytest.mark.parametrize("path", EXAMPLES, ids=lambda p: p.name)
def test_reasoning_matches_python(path):
    data = load_amt(path)
    edges, axioms = data["edges"], data["axioms"]
    py_edges, py_stats = reason_with_stats(edges, axioms)
    ok, py_violations = check_consistency(edges, axioms, reasoned=py_edges)

    js = _node({"op": "reason", "edges": edges, "axioms": axioms})

    assert len(js["edges"]) == len(py_edges)
    for mine, theirs in zip(js["edges"], py_edges):
        assert (mine["role"], mine["from"], mine["to"]) == (theirs["role"], theirs["from"], theirs["to"])
        assert mine["weight"] == pytest.approx(theirs["weight"], abs=1e-9)
        assert mine["inferred"] == theirs["inferred"]
        assert mine["provenance"] == theirs["provenance"]
        assert mine["type"] == theirs["type"]
        assert mine["method"] == theirs["method"]
    assert js["stats"]["iterations"] == py_stats["iterations"]
    assert js["consistency"]["consistent"] == ok
    assert js["consistency"]["violations"] == py_violations


def test_the_demo_has_derived_edges_with_type_and_method():
    """The comparison above is only worth something if some edges carry both."""
    data = load_amt(ROOT / "examples" / "hextuple-demo.ttl")
    got = _node({"op": "reason", "edges": data["edges"], "axioms": data["axioms"]})["edges"]
    derived = [e for e in got if e["inferred"]]
    assert any(e["method"] and e["type"] for e in derived)
    assert any(e["method"] and e["type"] is None for e in derived)
    assert any(e["method"] is None and e["type"] for e in derived)


def test_combine_types_matches_python():
    from amt.fw import FUZZINESS_WOBBLINESS, UNCERTAINTY, VAGUENESS, combine_types
    cases = [[], [None], [None, VAGUENESS], [UNCERTAINTY], [UNCERTAINTY, UNCERTAINTY], [UNCERTAINTY, None],
             [UNCERTAINTY, VAGUENESS, UNCERTAINTY], [FUZZINESS_WOBBLINESS, FUZZINESS_WOBBLINESS],
             [FUZZINESS_WOBBLINESS, UNCERTAINTY]]
    got = _node({"op": "combine", "cases": cases})
    assert got == [combine_types(c) for c in cases]


def test_equal_weight_tie_break_matches_python():
    from amt.core import AMT_PFX as A
    axioms = [
        {"type": "RoleChainAxiom", "iri": "http://x/axL", "antecedents": ["http://x/r1", "http://x/r2"],
         "consequent": "http://x/r3", "logic": A + "ProductLogic"},
        {"type": "RoleChainAxiom", "iri": "http://x/axG", "antecedents": ["http://x/r1", "http://x/r2"],
         "consequent": "http://x/r3", "logic": A + "GoedelLogic"},
    ]
    base = {"inferred": False, "provenance": [], "method": None, "evidence": None}
    edges = [dict(base, role="http://x/r1", **{"from": "http://x/a", "to": "http://x/b"}, weight=1.0, type=None),
             dict(base, role="http://x/r2", **{"from": "http://x/b", "to": "http://x/c"}, weight=0.5, type="http://w3id.org/fw_ontology/Uncertainty")]
    py = [e for e in do_reasoning(edges, axioms) if e["inferred"]]
    js = [e for e in _node({"op": "reason", "edges": edges, "axioms": axioms})["edges"] if e["inferred"]]
    assert [(e["weight"], e["type"], e["method"]) for e in js] == [(e["weight"], e["type"], e["method"]) for e in py]
    assert py[0]["method"] == A + "GoedelLogic"


LOGICS = [AMT_PFX + n for n in
          ("GoedelLogic", "ProductLogic", "LukasiewiczLogic", "EinsteinProduct", "GeometricMean", "HamacherProduct")]
GRID = [0.0, 0.1, 0.25, 0.5, 0.75, 0.85, 1.0]


def test_every_logic_matches_python_on_a_grid():
    cases = []
    for logic in LOGICS:
        param = 0.5 if logic.endswith("HamacherProduct") else None
        for n in (1, 2, 3):
            for ws in itertools.product(GRID, repeat=n):
                cases.append({"weights": list(ws), "logic": logic, "parameter": param})
    got = _node({"op": "aggregate", "cases": cases})
    for case, value in zip(cases, got):
        want = aggregate_weights(case["weights"], case["logic"], case["parameter"])
        assert value == pytest.approx(want, abs=1e-9), case


def test_normalise_builds_chains_from_the_legacy_pair_and_sorts_like_python():
    raw = [
        {"type": "RoleChainAxiom", "iri": "http://x/b", "antecedent1": "http://x/r1", "antecedent2": "http://x/r2",
         "consequent": "http://x/r3", "logic": AMT_PFX + "GoedelLogic"},
        {"type": "InverseAxiom", "iri": "http://x/a", "antecedent": "http://x/r1", "inverse": "http://x/r4"},
        {"type": "RoleChainAxiom", "iri": "http://x/a", "antecedents": ["http://x/r1"], "consequent": "http://x/r5",
         "logic": AMT_PFX + "HamacherProduct", "logicParameter": "0.5"},
    ]
    got = _node({"op": "normalise", "axioms": raw})
    assert [(a["type"], a["iri"]) for a in got] == [
        ("InverseAxiom", "http://x/a"), ("RoleChainAxiom", "http://x/a"), ("RoleChainAxiom", "http://x/b")]
    assert got[2]["antecedents"] == ["http://x/r1", "http://x/r2"]
    assert got[1]["logicParameter"] == 0.5
