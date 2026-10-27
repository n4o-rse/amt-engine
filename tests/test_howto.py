"""
Tests for the How-To pages (``py/site_howto.py``).

The examples on the pages are run, not just printed: a good example validates and
diagnoses clean, a bad one produces the message the page claims, and the SPARQL
recipe turns its sample input into a file that passes. Every code the engine can
report has an entry on the validate page.
"""
from __future__ import annotations

import re

import pytest
from rdflib import Graph

import site_howto as howto
from amt import load_amt
from amt.diagnostics import diagnose, has_errors
from amt.validation import validate_against_shapes


def _good():
    return [k for k, v in howto.EXAMPLES.items() if v["kind"] == "good"]


def _bad():
    return [k for k, v in howto.EXAMPLES.items() if v["kind"] == "bad"]


@pytest.mark.parametrize("key", _good())
def test_good_examples_pass_every_check(key):
    ttl = howto.EXAMPLES[key]["turtle"]
    result = validate_against_shapes(ttl)
    assert result.conforms, result.report_text
    assert not has_errors(diagnose(load_amt(ttl))), key


@pytest.mark.parametrize("key", _bad())
def test_bad_examples_fail_the_way_the_page_says(key):
    ex = howto.EXAMPLES[key]
    ttl = ex["turtle"]
    if ex["expect"] == "SHACL":
        assert not validate_against_shapes(ttl).conforms, key
    else:
        codes = [f.code for f in diagnose(load_amt(ttl))]
        assert ex["expect"] in codes, (key, codes)


def test_the_fixed_example_is_the_repair_of_the_broken_one():
    broken = {f.code for f in diagnose(load_amt(howto.EXAMPLES["bad-dangling"]["turtle"]))}
    fixed = {f.code for f in diagnose(load_amt(howto.EXAMPLES["fixed-dangling"]["turtle"]))}
    assert "AMT-E101" in broken and "AMT-E101" not in fixed


def test_construct_recipe_produces_a_valid_amt_file():
    data = Graph().parse(data=howto.CONSTRUCT_INPUT, format="turtle")
    out = data.query(howto.CONSTRUCT_QUERY).graph
    ttl = out.serialize(format="turtle")
    result = validate_against_shapes(ttl)
    assert result.conforms, result.report_text
    amt = load_amt(ttl)
    assert not has_errors(diagnose(amt))
    assert len(amt["concepts"]) == 2
    assert len(amt["nodes"]) == 7          # three coins with an edge, four emperors; the unknown one is no node
    assert sorted(round(e["weight"], 2) for e in amt["edges"]) == [0.5, 0.5, 0.6, 1.0]
    assert not [f for f in diagnose(amt) if f.code == "AMT-N302"]      # every node has a label (no blank-node authorities)


def test_every_code_of_the_engine_has_an_entry_on_the_validate_page():
    import amt.diagnostics as diag
    source = open(diag.__file__, encoding="utf-8").read()
    in_engine = set(re.findall(r"AMT-[EWN]\d{3}", source))
    documented = {row[0] for row in howto.CATALOGUE}
    assert in_engine <= documented, in_engine - documented
    html = howto.howto_validate()
    for code in documented:
        assert f'id="{code}"' in html


def test_pages_are_deterministic_and_have_no_clock():
    for make in howto.PAGES.values():
        assert make() == make()
        assert not re.search(r"\b20\d\d-\d\d-\d\d\b", make())


def test_pages_link_each_other_and_the_nav_has_the_entry():
    index = howto.howto_index()
    assert 'href="create/"' in index and 'href="validate/"' in index
    assert 'aria-current="page"' in index and ">How-To<" in index
