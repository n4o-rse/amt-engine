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
    ("How-To", "howto/", "howto"),
    ("Explorer", "explorer/", "explorer"),
    ("Bibliography", "bibliography/", "bibliography"),
    ("GitHub", "https://github.com/alpaca-fair-framework/amt-engine", "github"),
]


# (file in assets/img/logos/, name, address, display height in px): shown in the footer of every page.
LOGOS = [
    ("mainzed.png", "mainzed", "https://www.mainzed.org", 28),
    ("i3mainz.png", "i3mainz", "https://i3mainz.hs-mainz.de", 54),
    ("leiza.png", "LEIZA", "https://www.leiza.de", 54),
    ("nfdi4objects.png", "NFDI4Objects", "https://www.nfdi4objects.net", 54),
    ("nfdi.png", "Nationale Forschungsdateninfrastruktur (NFDI), in cooperation with", "https://www.nfdi.de", 66),
    ("dfg.png", "Deutsche Forschungsgemeinschaft (DFG), funded by", "https://www.dfg.de", 66),
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
    logos = '<div class="logos">' + "".join(
        f'<a href="{escape(url)}" title="{escape(name, quote=True)}"><img src="{up}assets/img/logos/{f}" '
        f'alt="{escape(name, quote=True)}" height="{h}"></a>'
        for f, name, url, h in LOGOS) + "</div>"
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
<a href="https://github.com/alpaca-fair-framework/amt-engine">source</a><br>
{logos}
A <strong>mainzed</strong> project of i3mainz (Hochschule Mainz) and the RGZM (today LEIZA), developed further in
NFDI4Objects, which is funded by the Deutsche Forschungsgemeinschaft (DFG, German Research Foundation) &ndash;
project number 501836407.
</footer>
</body>
</html>
"""
