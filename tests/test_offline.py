"""The pages load nothing from a third party, and every local link and file reference resolves."""
from __future__ import annotations

import re
from pathlib import Path
from urllib.parse import unquote, urlsplit

ROOT = Path(__file__).resolve().parent.parent
DOCS = ROOT / "docs"
PAGES = sorted(p for p in DOCS.rglob("*.html") if "vendor" not in p.parts)

LOAD = re.compile(r"""<(?:script|link|img|source|iframe)\b[^>]*?\b(?:src|href)\s*=\s*["']([^"']+)["']""", re.I)
ANY = re.compile(r"""\b(?:src|href)\s*=\s*["']([^"']+)["']""", re.I)
CSS_URL = re.compile(r"""url\(\s*["']?([^"')]+)["']?\s*\)""")


def _exists(base: Path, ref: str) -> bool:
    u = urlsplit(ref)
    if u.scheme or u.netloc or not u.path:
        return True                      # external or an in-page anchor: not our business here
    path = unquote(u.path).strip("\"'")
    t = (base.parent / path).resolve() if not path.startswith("/") else DOCS / path.lstrip("/")
    return (t / "index.html").exists() if t.is_dir() else t.exists()


def test_no_page_loads_a_script_style_or_image_from_elsewhere():
    for p in PAGES:
        for ref in LOAD.findall(p.read_text(encoding="utf-8")):
            assert not re.match(r"(https?:)?//", ref), f"{p.relative_to(ROOT)} loads {ref}"


def test_every_local_link_and_file_reference_resolves():
    for p in PAGES:
        for ref in ANY.findall(p.read_text(encoding="utf-8")):
            assert _exists(p, ref), f"{p.relative_to(ROOT)}: {ref} does not exist"


def test_stylesheets_load_nothing_from_elsewhere_and_their_files_exist():
    for css in sorted(DOCS.rglob("*.css")):
        for ref in CSS_URL.findall(css.read_text(encoding="utf-8")):
            if ref.startswith("data:"):
                continue
            assert not re.match(r"(https?:)?//", ref), f"{css.relative_to(ROOT)} loads {ref}"
            assert _exists(css, ref), f"{css.relative_to(ROOT)}: {ref} does not exist"


def test_vendored_libraries_come_with_their_licences():
    vendor = DOCS / "vendor"
    for lib in sorted(d for d in vendor.iterdir() if d.is_dir()):
        assert any(f.name.upper().startswith("LICENSE") for f in lib.iterdir()), lib.name
    assert (vendor / "README.md").exists()


def test_pyvis_export_embeds_its_library_by_default(tmp_path):
    from amt import load_amt
    from amt.viz import render_to_html
    a = load_amt(ROOT / "docs" / "data" / "animals.ttl")
    out = render_to_html(a["nodes"], a["edges"], a["concepts"], tmp_path / "g.html")
    html = out.read_text(encoding="utf-8")
    assert not re.search(r"<script[^>]+src=\"https?://", html) and not re.search(r"<link[^>]+href=\"https?://", html)
    remote = render_to_html(a["nodes"], a["edges"], a["concepts"], tmp_path / "r.html", cdn_resources="remote")
    assert re.search(r"<script[^>]+src=\"https?://", remote.read_text(encoding="utf-8"))


def test_pyvis_export_does_not_depend_on_the_platform_encoding(tmp_path):
    """On Windows pyvis writes with cp1252, which cannot hold the embedded library (found on the first Windows run)."""
    import os
    import subprocess
    import sys
    code = ("from amt import load_amt\nfrom amt.viz import render_to_html\n"
            f"a = load_amt(r'{ROOT / 'docs' / 'data' / 'animals.ttl'}')\n"
            f"render_to_html(a['nodes'], a['edges'], a['concepts'], r'{tmp_path / 'g.html'}')\n")
    env = {**os.environ, "PYTHONUTF8": "0", "PYTHONCOERCECLOCALE": "0", "LC_ALL": "C", "LANG": "C",
           "PYTHONPATH": str(ROOT)}
    r = subprocess.run([sys.executable, "-c", code], capture_output=True, text=True, env=env, cwd=tmp_path)
    assert r.returncode == 0, r.stderr[-600:]
    data = (tmp_path / "g.html").read_bytes()
    data.decode("utf-8")
    assert b"\r\n" not in data


def test_roboto_is_served_from_the_repository():
    """The pages use Roboto (the house typeface of mainzed) from docs/vendor/roboto/, not from a font server."""
    css = (DOCS / "assets" / "site.css").read_text(encoding="utf-8")
    assert "font-family: Roboto" in css and "Roboto, system-ui" in css
    for weight in (400, 500, 700):
        for subset in ("latin", "latin-ext"):
            assert f"roboto-{subset}-{weight}-normal.woff2" in css
            assert (DOCS / "vendor" / "roboto" / f"roboto-{subset}-{weight}-normal.woff2").exists()
    assert (DOCS / "vendor" / "roboto" / "LICENSE").exists()
    assert (ROOT / "design" / "fonts" / "LICENSE").exists()


def test_png_figures_are_drawn_with_the_same_typeface():
    import sys
    sys.path.insert(0, str(ROOT / "py"))
    from site_fonts import BOLD, REGULAR, fonts_digest, pil_font
    assert REGULAR.exists() and BOLD.exists()
    assert pil_font(20).getname() == ("Roboto", "Regular") and pil_font(20, True).getname() == ("Roboto", "Bold")
    assert pil_font(20).getlength("Größe") > 0        # the umlauts of German are in the file
    assert len(fonts_digest()) == 64
