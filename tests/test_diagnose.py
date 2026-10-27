"""
Tests for the plain-language diagnostics (``amt.diagnostics``), the formatted SHACL
violations and the runner options ``--check-only`` and ``--strict``.

The reference case is the one that started it: a file whose coins are instances
of a Concept while the authorities they point to are not. It used to end in an
``AssertionError`` from pyvis.
"""
from __future__ import annotations

from pathlib import Path

import pytest

from amt import load_amt
from amt.diagnostics import diagnose, has_errors
from amt.runner import main as runner_main
from amt.validation import format_violations, validate_against_shapes

ROOT = Path(__file__).resolve().parents[1]

PREFIXES = """@prefix amt: <http://academic-meta-tool.xyz/vocab#> .
@prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .
@prefix rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#> .
@prefix xsd: <http://www.w3.org/2001/XMLSchema#> .
@prefix ex: <http://example.org/> .
"""

# Coins are nodes, the authorities are not: the AFE case.
DANGLING = PREFIXES + """
ex:Coins a amt:Concept ; rdfs:label "Coins" .
ex:c1 amt:instanceOf ex:Coins ; rdfs:label "coin 1" .
[] rdf:subject ex:c1 ; rdf:predicate ex:hasAuthority ; rdf:object ex:vespasian ; amt:weight 0.5 .
[] rdf:subject ex:c1 ; rdf:predicate ex:hasAuthority ; rdf:object ex:titus ; amt:weight 0.5 .
ex:vespasian rdfs:label "vespasian" .
"""

FIXED = DANGLING + """
ex:Authority a amt:Concept ; rdfs:label "Authority" .
ex:vespasian amt:instanceOf ex:Authority .
ex:titus amt:instanceOf ex:Authority ; rdfs:label "titus" .
"""

CONCEPT_ITSELF = PREFIXES + """
ex:a amt:instanceOf amt:Concept ; rdfs:label "a" .
"""

UNDECLARED_CONCEPT = PREFIXES + """
ex:a amt:instanceOf ex:Thing ; rdfs:label "a" .
"""


def _codes(ttl: str) -> list[str]:
    return [f.code for f in diagnose(load_amt(ttl))]


def test_dangling_edge_ends_are_reported_with_their_iris():
    findings = diagnose(load_amt(DANGLING))
    e101 = [f for f in findings if f.code == "AMT-E101"]
    assert len(e101) == 1
    f = e101[0]
    assert f.level == "error"
    assert set(f.related) == {"http://example.org/vespasian", "http://example.org/titus"}
    text = f.format()
    assert "<http://example.org/titus> amt:instanceOf" in text      # paste-ready line per IRI
    assert has_errors(findings)


def test_fixed_file_has_no_errors():
    findings = diagnose(load_amt(FIXED))
    assert not has_errors(findings)


def test_instance_of_amt_concept_is_explained():
    f = [x for x in diagnose(load_amt(CONCEPT_ITSELF)) if x.code == "AMT-E102"]
    assert len(f) == 1
    assert "not a concept itself" in f[0].message
    assert "http://example.org/a" in f[0].message


def test_instance_of_undeclared_concept_is_reported():
    f = [x for x in diagnose(load_amt(UNDECLARED_CONCEPT)) if x.code == "AMT-E102"]
    assert len(f) == 1
    assert "http://example.org/Thing" in f[0].message
    assert "a amt:Concept" in f[0].hint


def test_statement_with_missing_part_is_reported():
    ttl = PREFIXES + """ex:C a amt:Concept ; rdfs:label "C" .
ex:a amt:instanceOf ex:C .
[] rdf:subject ex:a ; rdf:predicate ex:r ; amt:weight 0.5 .
"""
    f = [x for x in diagnose(load_amt(ttl)) if x.code == "AMT-E103"]
    assert len(f) == 1 and "rdf:object" in f[0].message


def test_empty_graph_warns():
    assert "AMT-W204" in _codes(PREFIXES + 'ex:C a amt:Concept ; rdfs:label "C" .\n')


def test_diagnostics_are_deterministic():
    a = [f.format() for f in diagnose(load_amt(DANGLING))]
    b = [f.format() for f in diagnose(load_amt(DANGLING))]
    assert a == b


def test_shipped_examples_have_no_diagnostic_errors():
    for ttl in sorted((ROOT / "examples").glob("*.ttl")):
        findings = diagnose(load_amt(ttl))
        assert not has_errors(findings), (ttl.name, [f.code for f in findings])


def test_shacl_violation_names_the_node_and_gives_a_hint():
    result = validate_against_shapes(UNDECLARED_CONCEPT)
    assert not result.conforms
    text = format_violations(result.violations)
    assert "ex:Thing" in text                       # which concept lacks the label
    assert 'rdfs:label "..."' in text               # what to add


def test_runner_no_longer_crashes_on_dangling_ends(tmp_path, capsys):
    src = tmp_path / "afe.ttl"
    src.write_text(DANGLING, encoding="utf-8")
    code = runner_main([str(src), "-o", str(tmp_path / "out")])
    out = capsys.readouterr().out
    assert code == 0
    assert "AMT-E101" in out
    html = (tmp_path / "out" / "afe.html").read_text(encoding="utf-8")
    assert "http://example.org/titus" in html       # drawn as a placeholder node


def test_check_only_writes_nothing(tmp_path, capsys):
    src = tmp_path / "afe.ttl"
    src.write_text(FIXED, encoding="utf-8")
    code = runner_main([str(src), "--check-only"])
    assert code == 0
    assert not (tmp_path / "out").exists()
    assert "nothing was written" in capsys.readouterr().out


def test_strict_turns_diagnostic_errors_into_exit_code_1(tmp_path):
    src = tmp_path / "afe.ttl"
    src.write_text(DANGLING, encoding="utf-8")
    assert runner_main([str(src), "--check-only", "--strict"]) == 1
    src.write_text(FIXED, encoding="utf-8")
    assert runner_main([str(src), "--check-only", "--strict"]) == 0


def test_unexpected_errors_get_a_short_message(tmp_path, capsys, monkeypatch):
    import amt.runner as runner

    def boom(*a, **k):
        raise RuntimeError("kaputt")

    monkeypatch.setattr(runner, "render_to_html", boom)
    src = tmp_path / "x.ttl"
    src.write_text(FIXED, encoding="utf-8")
    assert runner.main([str(src), "-o", str(tmp_path / "o")]) == 3
    err = capsys.readouterr().err
    assert "Unexpected error: RuntimeError: kaputt" in err and "--debug" in err
    with pytest.raises(RuntimeError):
        runner.main([str(src), "-o", str(tmp_path / "o"), "--debug"])
