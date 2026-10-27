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
