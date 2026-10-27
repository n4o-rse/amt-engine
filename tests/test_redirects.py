"""deploy/redirects.yaml: the targets exist, the generated files are current, the rules answer as intended."""
from __future__ import annotations

from pathlib import Path

import site_redirects as sr

ROOT = Path(__file__).resolve().parent.parent
DOCS = ROOT / "docs"
BROWSER = "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8"


def test_every_local_target_exists_in_docs():
    cfg = sr.load()
    for t in sr.local_targets(cfg):
        p = DOCS / t
        assert (p / "index.html").exists() if (t == "" or t.endswith("/")) else p.exists(), t


def test_generated_files_are_current():
    for path, text in sr.outputs().items():
        assert path.read_text(encoding="utf-8").replace("\r\n", "\n") == text, path.relative_to(ROOT)


def test_vocabulary_is_negotiated_on_both_sites():
    cfg = sr.load()
    for site, status in (("academic-meta-tool.xyz", 303), ("w3id", 302)):
        for path in ("vocab", "vocab/"):
            for accept, key in (("text/turtle", "turtle"), ("application/rdf+xml", "rdfxml"),
                                ("application/ld+json", "jsonld"), (BROWSER, "html"), ("", "html")):
                assert sr.resolve(cfg, site, path, accept) == (status, cfg["pages"] + cfg["vocab"][key]), (site, accept)


def test_old_addresses_keep_working_and_unknown_ones_do_not_match():
    cfg = sr.load()
    assert sr.resolve(cfg, "academic-meta-tool.xyz", "amt.rdf") == (301, cfg["pages"] + "vocab/amt.rdf")
    assert sr.resolve(cfg, "academic-meta-tool.xyz", "ontology/")[1] == cfg["pages"] + "ontology/"
    assert sr.resolve(cfg, "academic-meta-tool.xyz", "") == (302, cfg["pages"])
    assert sr.resolve(cfg, "w3id", "nothing") is None


def test_htaccess_has_one_rule_set_per_route_and_no_catch_all():
    cfg = sr.load()
    for name in cfg["sites"]:
        text = sr.render_htaccess(cfg, name)
        assert "RewriteEngine On" in text and "(.*)" not in text
        assert text.count("RewriteRule") == sum(4 if r.get("vocab") else 1 for r in cfg["sites"][name]["routes"])
    assert "RewriteBase /ids/amt/" in sr.render_htaccess(cfg, "w3id")


def test_namespace_is_the_one_in_the_ontology():
    ttl = (ROOT / "ontology" / "amt.ttl").read_text(encoding="utf-8")
    cfg = sr.load()
    assert "http://academic-meta-tool.xyz/vocab#" in ttl
    assert cfg["sites"]["academic-meta-tool.xyz"]["base_url"] + "vocab" == "http://academic-meta-tool.xyz/vocab"
