"""
Tests for the generated vocabulary and ontology pages (step ``site``).

They check the decisions behind the generator, not the look of a page: that
every term of ``ontology/amt.ttl`` reaches the vocabulary page, that the figures
cannot fall behind the ontology, that every Turtle example on the ontology page
is valid AMT, and that the SVG output is deterministic.
"""
from __future__ import annotations

import xml.etree.ElementTree as ET
from pathlib import Path

import pytest
from rdflib import RDF, RDFS, Graph

import site_figures as figs
import site_pages as pages
from amt import validate_against_shapes

ROOT = Path(__file__).resolve().parent.parent
AMT = pages.AMT


@pytest.fixture(scope="module")
def graph() -> Graph:
    return Graph().parse(ROOT / "ontology" / "amt.ttl", format="turtle")


def _all_figures(graph: Graph) -> dict:
    scenes = {name: make() for name, make in figs.SMALL_FIGURES.items()}
    scenes["overview"] = figs.overview_scene(graph)
    return scenes


def test_vocabulary_page_has_a_card_for_every_term(graph):
    html = pages.vocab_page(graph, "<svg></svg>")
    terms = {str(s)[len(AMT):] for s in set(graph.subjects()) if str(s).startswith(AMT) and len(str(s)) > len(AMT)}
    missing = sorted(t for t in terms if f'id="{t}"' not in html)
    assert not missing, f"terms of amt.ttl without a card on the page: {missing}"


def test_terms_of_2018_are_not_marked_as_new(graph):
    html = pages.vocab_page(graph, "<svg></svg>")
    # SubsumptionAxiom is new, Concept is not: only the first card carries the badge
    card = lambda t: html.split(f'id="{t}"', 1)[1].split("</h3>", 1)[0]
    assert "added since 2018" in card("SubsumptionAxiom")
    assert "added since 2018" not in card("Concept")
    # and the list of 2018 terms is a subset of the terms that exist today
    assert all(URI_exists(graph, t) for t in pages.PENNY_TERMS)


def URI_exists(graph: Graph, local: str) -> bool:
    from rdflib import URIRef
    return (URIRef(AMT + local), None, None) in graph


def test_every_ontology_example_parses_and_validates():
    ttl = pages.PREFIXES + "\n" + "\n\n".join(pages.SNIPPETS.values()) + "\n"
    g = Graph().parse(data=ttl, format="turtle")      # a syntax error fails here
    assert len(g) > 0
    result = validate_against_shapes(ttl)
    assert result.conforms, result.report_text


def test_ontology_page_shows_every_example(graph):
    figures = {n: "<svg></svg>" for n in figs.SMALL_FIGURES}
    html = pages.ontology_page(graph, figures)
    for key, text in pages.SNIPPETS.items():
        first = text.splitlines()[0]
        assert first.split()[0] in html, f"example {key} is not on the page"


def test_overview_follows_the_ontology(graph):
    scene = figs.overview_scene(graph)
    boxes = {k for k, n in scene.nodes.items() if n.kind == "box"}
    classes = {str(c)[len(AMT):] for c in graph.subjects(RDF.type, RDFS.Class) if str(c).startswith(AMT)}
    assert classes <= boxes, f"classes without a box: {sorted(classes - boxes)}"


def test_overview_fails_when_a_class_has_no_position(graph, monkeypatch):
    graph2 = Graph()
    for t in graph:
        graph2.add(t)
    graph2.parse(data=pages.PREFIXES + "amt:BrandNewAxiom a rdfs:Class .", format="turtle")
    with pytest.raises(SystemExit, match="BrandNewAxiom"):
        figs.overview_scene(graph2)


def test_svg_is_valid_xml_and_deterministic(graph):
    for name, scene in _all_figures(graph).items():
        first, second = figs.render_svg(scene), figs.render_svg(scene)
        assert first == second, name
        root = ET.fromstring(first)                  # well-formed
        assert root.tag.endswith("svg"), name
        assert "\r" not in first, name               # LF only, on every platform


def test_every_circle_label_is_drawn(graph):
    svg = figs.render_svg(figs.fig_rca())
    for label in ("antecedent1", "antecedent2", "consequent, logic"):
        assert label in svg


def test_symbols_are_vector_lines_not_font_glyphs():
    sc = figs.Scene("t", 100, 100, "t")
    sc.symbol("notin", 50, 50)
    svg = figs.render_svg(sc)
    assert "<path" in svg and "∉" not in svg
    with pytest.raises(ValueError):
        sc.symbol("nonsense", 1, 1)


def test_png_is_three_times_the_svg_size(tmp_path):
    pytest.importorskip("PIL")
    from PIL import Image
    scene = figs.fig_concept()
    out = tmp_path / "c.png"
    figs.render_png(scene, out)
    with Image.open(out) as im:
        assert im.size == (scene.w * figs.PNG_SCALE, scene.h * figs.PNG_SCALE)
        assert im.mode == "RGBA"
