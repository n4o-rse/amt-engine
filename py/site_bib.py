"""
The bibliography page: works that use or describe AMT, from ``data/bibliography.bib``.

BibTeX is the source (one file, easy to extend, importable by Zotero); the page
shows every entry in APA 7 style, grouped by the field ``kind`` (paper, talk,
software, dataset, other), together with the entry's own BibTeX for copying.
The parser reads the small subset of BibTeX that the file uses; it has no
dependency and no clock, so the page changes only when the .bib changes.

Entry types: ``article``, ``inproceedings``, ``misc`` (talks, software, data).
Unknown types are rendered as ``misc``.
"""
from __future__ import annotations

import re
from html import escape
from pathlib import Path

try:
    from amt_site import page
except ImportError:
    from py.amt_site import page

ROOT = Path(__file__).resolve().parent.parent
BIB_FILE = ROOT / "data" / "bibliography.bib"
REPO_BIB_URL = "https://github.com/n4o-rse/amt-engine/blob/main/data/bibliography.bib"

# order of the groups on the page: (kind, English heading, German heading)
KINDS = [
    ("paper", "Papers and articles", "Aufsätze und Artikel"),
    ("talk", "Talks and posters", "Vorträge und Poster"),
    ("software", "Software and code", "Software und Code"),
    ("dataset", "Data", "Daten"),
    ("other", "Other", "Weiteres"),
]


# ------------------------------------------------------------------ parsing
class BibError(ValueError):
    pass


def _read_braced(text: str, i: int) -> tuple[str, int]:
    """``text[i]`` is ``{``: return (content without the outer braces, index after the closing brace)."""
    depth, j = 0, i
    while j < len(text):
        c = text[j]
        if c == "{":
            depth += 1
        elif c == "}":
            depth -= 1
            if depth == 0:
                return text[i + 1:j], j + 1
        j += 1
    raise BibError("unbalanced braces in the .bib file")


def parse(text: str) -> list[dict]:
    """Entries in file order: ``{"type", "key", "fields": {name: value}, "raw": original text}``."""
    entries = []
    for m in re.finditer(r"^@(\w+)\s*\{", text, re.M):
        body, end = _read_braced(text, m.end() - 1)
        key, _, rest = body.partition(",")
        fields = {}
        pos = 0
        while True:
            fm = re.compile(r"\s*(\w+)\s*=\s*").match(rest, pos)
            if not fm:
                break
            j = fm.end()
            if rest[j] == "{":
                val, j = _read_braced(rest, j)
            elif rest[j] == '"':
                k = rest.index('"', j + 1)
                val, j = rest[j + 1:k], k + 1
            else:
                k = re.compile(r"[^,\s}]+").match(rest, j)
                val, j = k.group(0), k.end()
            fields[fm.group(1).lower()] = re.sub(r"\s+", " ", val).strip()
            pos = j
            cm = re.compile(r"\s*,").match(rest, pos)
            pos = cm.end() if cm else pos
        entries.append({"type": m.group(1).lower(), "key": key.strip(), "fields": fields,
                        "raw": text[m.start():end].rstrip()})
    return entries


def check(entries: list[dict]) -> list[str]:
    """Problems that would make the page wrong: missing key, author, year, title, DOI or URL, duplicate keys."""
    bad, seen = [], set()
    for e in entries:
        f, k = e["fields"], e["key"]
        if not k or k in seen:
            bad.append(f"{k or '(no key)'}: key missing or used twice")
        seen.add(k)
        for need in ("author", "year", "title"):
            if not f.get(need):
                bad.append(f"{k}: field {need} is missing")
        if not (f.get("doi") or f.get("url")):
            bad.append(f"{k}: neither doi nor url")
        if f.get("kind", "other") not in dict((a, b) for a, b, _ in KINDS):
            bad.append(f"{k}: unknown kind {f.get('kind')!r}")
    return bad


# ------------------------------------------------------------------ APA 7
def _clean(s: str) -> str:
    return s.replace("{", "").replace("}", "")


def _initials(given: str) -> str:
    """``Allard W.`` -> ``A. W.``; ``Jean-Luc`` -> ``J.-L.``"""
    return " ".join("-".join(p.rstrip(".")[0].upper() + "." for p in w.split("-") if p.rstrip("."))
                    for w in given.split())


def authors(field: str) -> list[tuple[str, str]]:
    """[(family, initials)] from ``Last, First and Last, First``; a name without comma is ``First Last``."""
    out = []
    for a in re.split(r"\s+and\s+", _clean(field)):
        if "," in a:
            fam, _, giv = a.partition(",")
        else:
            *giv_l, fam = a.split()
            giv = " ".join(giv_l)
        out.append((fam.strip(), _initials(giv.strip())))
    return out


def apa_authors(field: str) -> str:
    a = [f"{fam}, {ini}".rstrip(", ") for fam, ini in authors(field)]
    if len(a) == 1:
        return a[0]
    if len(a) > 20:
        a = a[:19] + ["… " + a[-1]]
        return ", ".join(a)
    return ", ".join(a[:-1]) + ", & " + a[-1]


def _end(s: str) -> str:
    """Add a full stop unless the text ends in punctuation."""
    s = s.rstrip()
    return s if s[-1:] in ".?!" else s + "."


def _link(f: dict) -> str:
    if f.get("doi"):
        u = "https://doi.org/" + f["doi"]
    elif f.get("url"):
        u = f["url"]
    else:
        return ""
    return f'<a href="{escape(u, quote=True)}">{escape(u)}</a>'


def apa(e: dict) -> str:
    """One reference in APA 7 style as HTML (journal, volume and book titles in <em>)."""
    f, t = e["fields"], e["type"]
    head = f"{escape(apa_authors(f['author']))} ({escape(f['year'])}). "
    title = escape(_clean(f["title"]))
    pages = escape(f["pages"].replace("--", "–")) if f.get("pages") else ""
    if t == "article":
        vol = f.get("volume", "")
        src = f'<em>{escape(_clean(f.get("journal", "")))}</em>'
        if vol:
            src += f', <em>{escape(vol)}</em>'
        if f.get("number"):
            src += f'({escape(f["number"])})'
        if f.get("issuetitle"):
            src += f' ({escape(_clean(f["issuetitle"]))})'
        if pages:
            src += f", {pages}"
        body = f"{_end(title)} {_end(src)}"
    elif t == "inproceedings":
        src = f'In <em>{escape(_clean(f.get("booktitle", "")))}</em>'
        if pages:
            src += f" (pp. {pages})"
        body = f"{_end(title)} {_end(src)}"
        if f.get("publisher"):
            body += f' {_end(escape(f["publisher"]))}'
    else:
        kind = f.get("howpublished", "")
        body = f"<em>{_end_in_em(title)}</em>" + (f" [{escape(kind)}]" if kind else "") + "."
        if f.get("publisher"):
            body += f' {_end(escape(f["publisher"]))}'
    note = f' {_end(escape(f["note"]))}' if f.get("note") else ""
    link = _link(f)
    return (head + body + note + (" " + link if link else "")).strip()


def _end_in_em(s: str) -> str:
    return s.rstrip(".")


def sort_key(e: dict):
    first = authors(e["fields"]["author"])
    return ([(fam.lower(), ini) for fam, ini in first], e["fields"]["year"], e["key"])


# ------------------------------------------------------------------ page
TEXT = {
    "en": {
        "h": "Bibliography",
        "lead": "Papers, talks and software that use or describe the Academic Meta Tool, in APA 7 style.",
        "empty": "Nothing here yet.",
        "add": 'Do you use AMT and want your work listed? Send an entry as BibTeX (issue or pull request) for '
               f'<a href="{REPO_BIB_URL}"><code>data/bibliography.bib</code></a>.',
        "dl": "Download all as BibTeX",
    },
    "de": {
        "h": "Bibliografie",
        "lead": "Aufsätze, Vorträge und Software, die das Academic Meta Tool verwenden oder beschreiben, im Stil von APA 7.",
        "empty": "Hier steht noch nichts.",
        "add": 'Du nutzt AMT und möchtest deine Arbeit hier sehen? Schick einen Eintrag als BibTeX (Issue oder Pull '
               f'Request) für <a href="{REPO_BIB_URL}"><code>data/bibliography.bib</code></a>.',
        "dl": "Alles als BibTeX laden",
    },
}


def _both(key: str, tag: str = "span") -> str:
    return "".join(f'<{tag} data-l="{l}" lang="{l}">{TEXT[l][key]}</{tag}>' for l in ("en", "de"))


def bibliography_page(entries: list[dict]) -> str:
    groups = []
    for kind, en, de in KINDS:
        items = sorted((e for e in entries if e["fields"].get("kind", "other") == kind), key=sort_key)
        if not items:
            continue
        lis = "".join(
            f'<li id="{escape(e["key"], quote=True)}">{apa(e)}'
            f'<details class="bibtex"><summary>BibTeX</summary><pre><code>{escape(e["raw"])}</code></pre></details></li>'
            for e in items)
        groups.append(f'<h2><span data-l="en" lang="en">{escape(en)}</span>'
                      f'<span data-l="de" lang="de">{escape(de)}</span></h2>\n<ul class="refs">{lis}</ul>')
    body = "\n".join(groups) or _both("empty", "p")
    body = (f'<h1>{_both("h")}</h1>\n<p class="lead">{_both("lead")}</p>\n{body}\n'
            f'<p class="note">{_both("add")}</p>\n'
            f'<div class="btns"><a class="btn" href="amt.bib" download>{_both("dl")}</a></div>')
    return page(title="Bibliography", body=body, depth=1, current="bibliography", lang_switch=True,
                description="Papers, talks and software that use or describe the Academic Meta Tool.")


def load(path: Path = BIB_FILE) -> list[dict]:
    return parse(path.read_text(encoding="utf-8"))
