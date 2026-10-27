"""
Page frame shared by the generated static pages in ``docs/``.

Kept apart from ``amt_dev_utils`` so that the page skeleton (header, footer,
stylesheet link) is one thing to change. Pages in a sub-folder of ``docs/``
pass ``depth=1`` so that the links reach back up to the shared files.

No clock is read: the footer names the release, not the build time.
"""
from __future__ import annotations

from html import escape

try:
    from amt_dev_utils import RELEASE
except ImportError:
    from py.amt_dev_utils import RELEASE

# (label, path relative to docs/, key).
NAV = [
    ("Home", "index.html", "home"),
    ("Vocabulary", "vocab/", "vocab"),
    ("Data model", "ontology/", "ontology"),
    ("Explorer", "explorer/", "explorer"),
    ("GitHub", "https://github.com/n4o-rse/amt-engine", "github"),
]


def page(*, title: str, body: str, depth: int, current: str, description: str = "", lang_switch: bool = False) -> str:
    """Wrap ``body`` into a complete HTML page. Output uses LF line ends only."""
    up = "../" * depth
    nav = "".join(
        '<a href="{h}"{c}>{t}</a>'.format(
            h=escape(p if p.startswith("http") else up + p),
            t=escape(t),
            c=' aria-current="page"' if k == current else "",
        )
        for t, p, k in NAV
    )
    lang_btn = ('<button type="button" class="theme push" id="lang-toggle" '
                'aria-label="Switch language: English or German">Deutsch</button>') if lang_switch else ""
    theme_extra = "" if lang_switch else " push"
    desc = f'<meta name="description" content="{escape(description, quote=True)}">\n' if description else ""
    return f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{escape(title)}</title>
{desc}<link rel="icon" type="image/png" href="{up}assets/img/amt-penguin-small.png">
<link rel="stylesheet" href="{up}assets/palette.css">
<link rel="stylesheet" href="{up}assets/site.css">
<script src="{up}assets/site.js"></script>
</head>
<body>
<header class="site"><div class="in">
<a class="brand" href="{up}index.html"><img src="{up}assets/img/amt-penguin-small.png" alt="" width="34" height="48">Academic Meta Tool</a>
<nav>{nav}</nav>
{lang_btn}<button type="button" class="theme{theme_extra}" id="theme-toggle" aria-label="Switch between light and dark mode">Dark mode</button>
</div></header>
<main>
{body}
</main>
<footer class="site">
Academic Meta Tool &middot; amt-engine {escape(RELEASE)} &middot;
<a href="https://github.com/n4o-rse/amt-engine">source</a><br>
<img class="partners" src="{up}assets/img/partners.png" alt="mainzed, i3mainz, LEIZA" height="40"><br>
A <strong>mainzed</strong> project of i3mainz (Hochschule Mainz) and the RGZM (today LEIZA), developed further in
NFDI4Objects, which is funded by the Deutsche Forschungsgemeinschaft (DFG, German Research Foundation) &ndash;
project number 501836407.
</footer>
</body>
</html>
"""
