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
    assert js["stats"]["iterations"] == py_stats["iterations"]
    assert js["consistency"]["consistent"] == ok
    assert js["consistency"]["violations"] == py_violations


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
