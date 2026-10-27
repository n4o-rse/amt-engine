"""
Persistent addresses of AMT, from ``deploy/redirects.yaml``.

One YAML file describes two redirect layers (the FTP of academic-meta-tool.xyz
and the entry at w3id.org/ids/amt/). From it come

* the two ``.htaccess`` files and the README of the w3id entry (``render_*``), and
* ``resolve()``: what a request must answer, as (status, Location). The
  tests use it to check that every target exists in ``docs/``, and
  ``py/check_redirects.py`` compares the live servers with it.

Nothing here reads the clock; the output depends on the YAML alone.
"""
from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
REDIRECTS_FILE = ROOT / "deploy" / "redirects.yaml"

# Accept header -> key under `vocab:` (first match wins), as regular
# expressions the same way in Apache and in resolve().
NEGOTIATION = [
    ("turtle", r"text/turtle|application/x-turtle"),
    ("rdfxml", r"application/rdf\+xml"),
    ("jsonld", r"application/(ld\+)?json"),
]


def load(path: Path = REDIRECTS_FILE) -> dict:
    import yaml
    return yaml.safe_load(path.read_text(encoding="utf-8"))


def _target(cfg: dict, to: str) -> str:
    return to if to.startswith("http") else cfg["pages"] + to


def resolve(cfg: dict, site: str, path: str, accept: str = "") -> tuple[int, str] | None:
    """(status, absolute Location) for ``path`` below the site's base, or None if no rule matches."""
    s = cfg["sites"][site]
    path = path.strip("/")
    for r in s["routes"]:
        if r["path"] != path:
            continue
        if r.get("vocab"):
            for key, rx in NEGOTIATION:
                if re.search(rx, accept or ""):
                    return s["vocab_status"], _target(cfg, cfg["vocab"][key])
            return s["vocab_status"], _target(cfg, cfg["vocab"]["html"])
        return r.get("status", s["status"]), _target(cfg, r["to"])
    return None


def local_targets(cfg: dict) -> list[str]:
    """Every target on our own pages (relative to ``pages``), without duplicates, sorted."""
    out = set(cfg["vocab"].values())
    for s in cfg["sites"].values():
        for r in s["routes"]:
            if "to" in r and not r["to"].startswith("http"):
                out.add(r["to"])
    return sorted(out)


# ---------------------------------------------------------------- .htaccess
def _pattern(path: str) -> str:
    esc = re.escape(path).replace("\\/", "/")
    return "^$" if path == "" else f"^{esc}/?$"


def render_htaccess(cfg: dict, site: str) -> str:
    s = cfg["sites"][site]
    L = ["# Generated from deploy/redirects.yaml by py/site_redirects.py. Do not edit.",
         "RewriteEngine On"]
    if "rewrite_base" in s:
        L.append(f"RewriteBase {s['rewrite_base']}")
    L.append("")
    for r in s["routes"]:
        pat = _pattern(r["path"])
        if r.get("vocab"):
            st = s["vocab_status"]
            L.append("# The vocabulary: content negotiation on the Accept header")
            for key, rx in NEGOTIATION:
                L.append(f"RewriteCond %{{HTTP_ACCEPT}} {rx}")
                L.append(f"RewriteRule {pat} {_target(cfg, cfg['vocab'][key])} [R={st},L]")
            L.append(f"RewriteRule {pat} {_target(cfg, cfg['vocab']['html'])} [R={st},L]")
        else:
            st = r.get("status", s["status"])
            L.append(f"RewriteRule {pat} {_target(cfg, r['to'])} [R={st},L]")
        L.append("")
    return "\n".join(L).rstrip("\n") + "\n"


def render_w3id_readme(cfg: dict) -> str:
    s = cfg["sites"]["w3id"]
    m = cfg["w3id_readme"]
    rows = ["| Address | Leads to |", "|---|---|"]
    for r in s["routes"]:
        addr = s["base_url"] + r["path"]
        if r.get("vocab"):
            rows.append(f"| {addr} | {_target(cfg, cfg['vocab']['html'])} (HTML); Turtle, RDF/XML and JSON-LD "
                        "by content negotiation |")
        else:
            rows.append(f"| {addr} | {_target(cfg, r['to'])} |")
    contacts = "\n".join(f"* {c}" for c in m["contacts"])
    return (f"## {m['title']}\n\n{m['text']}\n\n## Redirections\n\n" + "\n".join(rows) +
            f"\n\n## Contacts\n\n{contacts}\n")


def outputs(cfg: dict | None = None) -> dict[Path, str]:
    """All generated files: path -> text."""
    cfg = cfg or load()
    out = {}
    for name, s in cfg["sites"].items():
        out[ROOT / s["file"]] = render_htaccess(cfg, name)
        if "readme" in s:
            out[ROOT / s["readme"]] = render_w3id_readme(cfg)
    return out
