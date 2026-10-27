"""
Step ``site`` — generate the start, vocabulary and ontology pages from ``ontology/amt.ttl``.

Writes, below ``docs/``:

    index.html                the start page (English and German, light and dark)
    vocab/index.html          the vocabulary page (every term of amt.ttl)
    vocab/amt.ttl             a copy of ontology/amt.ttl
    vocab/amt.rdf             the same graph as RDF/XML
    vocab/amt.jsonld          the same graph as JSON-LD
    vocab/amt-overview.svg|png  overview figure, drawn from the ontology
    bibliography/index.html   the bibliography (APA 7), from data/bibliography.bib
    bibliography/amt.bib      a copy of data/bibliography.bib
    ontology/index.html       the data model page
    ontology/img/*.svg|png    the small figures of that page
    assets/palette.css        the colours of every page, from design/palette.yaml
    assets/img/palette.svg|png  the palette as a picture
    assets/figures.json       SHA-256 of every figure SVG (see below)

and, outside docs/, the redirect files of deploy/ (the FTP of academic-meta-tool.xyz
and the w3id.org entry) from deploy/redirects.yaml.

Nothing is written when nothing changed, and nothing reads the clock, so two
runs leave ``git status`` clean. A file that had to be written is a warning; in
``--strict`` mode that fails the step, which makes the step a drift check for
CI exactly like ``docs-sync``.

What is compared how:

* HTML, Turtle, SVG and the manifest are text: compared with line ends
  normalised (CRLF counts as LF), written with LF.
* RDF/XML and JSON-LD are compared as *graphs* (isomorphism), not as bytes:
  the byte layout of a serialiser can change between rdflib releases, the
  content cannot.
* PNG files are derived from the SVGs. Their bytes depend on the Pillow and
  FreeType build, so they are not compared; a PNG is redrawn only when its SVG
  changed (``figures.json``) or the PNG is missing.

Standalone:  python py/step_site.py
"""
from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

from rdflib import Graph
from rdflib.compare import isomorphic

try:
    from amt_dev_utils import DOCS_DIR, ONTOLOGY_DIR, ROOT, Report
    import site_figures as figs
    import site_pages as pages
    import site_palette as palette
    import site_redirects as redirects
    import site_bib as bib
    from site_home import home_page
except ImportError:  # imported as py.step_site from the repository root
    from py.amt_dev_utils import DOCS_DIR, ONTOLOGY_DIR, ROOT, Report
    from py import site_figures as figs
    from py import site_pages as pages
    from py import site_palette as palette
    from py import site_redirects as redirects
    from py import site_bib as bib
    from py.site_home import home_page

MANIFEST = DOCS_DIR / "assets" / "figures.json"


def _norm(b: bytes) -> bytes:
    return b.replace(b"\r\n", b"\n")


def _rel(p: Path) -> str:
    return p.relative_to(ROOT).as_posix()


def _write_text(rep: Report, path: Path, text: str, counts: dict) -> None:
    data = text.replace("\r\n", "\n").encode("utf-8")
    if path.exists() and _norm(path.read_bytes()) == data:
        counts["same"] += 1
        return
    verb = "updated" if path.exists() else "created"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(data)
    rep.warn(f"{verb} {_rel(path)}")


def _write_graph(rep: Report, path: Path, g: Graph, fmt: str, counts: dict) -> None:
    parse_fmt = "xml" if fmt == "pretty-xml" else fmt     # the serializer name is not a parser name
    if path.exists():
        try:
            if isomorphic(Graph().parse(path, format=parse_fmt), g):
                counts["same"] += 1
                return
        except Exception:  # an unreadable file is simply rewritten
            pass
    verb = "updated" if path.exists() else "created"
    path.parent.mkdir(parents=True, exist_ok=True)
    data = g.serialize(format=fmt)
    path.write_bytes(data.replace("\r\n", "\n").encode("utf-8") if isinstance(data, str) else data)
    rep.warn(f"{verb} {_rel(path)}")


def main() -> int:
    rep = Report("site")
    ttl_path = ONTOLOGY_DIR / "amt.ttl"
    g = Graph().parse(ttl_path, format="turtle")
    counts = {"same": 0}

    # 1. figures: scenes -> SVG text
    scenes = {name: make() for name, make in figs.SMALL_FIGURES.items()}
    scenes["overview"] = figs.overview_scene(g)
    where = {name: DOCS_DIR / "ontology" / "img" / name for name in figs.SMALL_FIGURES}
    where["overview"] = DOCS_DIR / "vocab" / "amt-overview"
    svg = {name: figs.render_svg(sc) for name, sc in scenes.items()}

    # 2. PNGs follow the SVGs through the manifest
    old = json.loads(MANIFEST.read_text(encoding="utf-8")) if MANIFEST.exists() else {}
    new = {}
    redrawn = 0
    for name in sorted(scenes):
        base = where[name]
        digest = hashlib.sha256(svg[name].encode("utf-8")).hexdigest()
        new[_rel(base.with_suffix(".svg"))] = digest
        png = base.with_suffix(".png")
        if not png.exists() or old.get(_rel(base.with_suffix(".svg"))) != digest:
            try:
                figs.render_png(scenes[name], png)
            except ImportError:
                return rep.fail("Pillow is needed to draw the PNG figures: pip install -r requirements.txt")
            redrawn += 1
            rep.warn(f"drew {_rel(png)}")
        _write_text(rep, base.with_suffix(".svg"), svg[name], counts)

    # 2b. the palette: CSS variables for every page, and the picture of it
    pal = palette.load()
    _write_text(rep, DOCS_DIR / "assets" / "palette.css", palette.css(pal), counts)
    pal_base = DOCS_DIR / "assets" / "img" / "palette"
    pal_svg = palette.svg(pal)
    pal_digest = hashlib.sha256(pal_svg.encode("utf-8")).hexdigest()
    new[_rel(pal_base.with_suffix(".svg"))] = pal_digest
    if not pal_base.with_suffix(".png").exists() or old.get(_rel(pal_base.with_suffix(".svg"))) != pal_digest:
        try:
            palette.render_png(pal_base.with_suffix(".png"), pal)
        except ImportError:
            return rep.fail("Pillow is needed to draw the PNG figures: pip install -r requirements.txt")
        rep.warn(f"drew {_rel(pal_base.with_suffix('.png'))}")
    _write_text(rep, pal_base.with_suffix(".svg"), pal_svg, counts)
    _write_text(rep, MANIFEST, json.dumps(new, indent=2, sort_keys=True) + "\n", counts)

    # 2c. the redirect files for the FTP of academic-meta-tool.xyz and for w3id.org
    for path, text in redirects.outputs().items():
        _write_text(rep, path, text, counts)

    # 3. pages and ontology files
    inline = {name: svg[name] for name in figs.SMALL_FIGURES}
    _write_text(rep, DOCS_DIR / "index.html", home_page(), counts)
    _write_text(rep, DOCS_DIR / "vocab" / "index.html", pages.vocab_page(g, svg["overview"]), counts)
    _write_text(rep, DOCS_DIR / "ontology" / "index.html", pages.ontology_page(g, inline), counts)
    entries = bib.load()
    for line in bib.check(entries):
        rep.warn(f"bibliography: {line}")
    _write_text(rep, DOCS_DIR / "bibliography" / "index.html", bib.bibliography_page(entries), counts)
    _write_text(rep, DOCS_DIR / "bibliography" / "amt.bib", bib.BIB_FILE.read_text(encoding="utf-8"), counts)
    _write_text(rep, DOCS_DIR / "vocab" / "amt.ttl", ttl_path.read_text(encoding="utf-8"), counts)
    _write_graph(rep, DOCS_DIR / "vocab" / "amt.rdf", g, "pretty-xml", counts)
    _write_graph(rep, DOCS_DIR / "vocab" / "amt.jsonld", g, "json-ld", counts)

    rep.ok(f"{counts['same']} generated file(s) already up to date; {len(scenes)} figures, {redrawn} PNG(s) redrawn")
    return rep.finish()


if __name__ == "__main__":
    sys.exit(main())
