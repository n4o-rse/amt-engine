#!/usr/bin/env python3
"""
Compare the live redirect servers with ``deploy/redirects.yaml``.

Run it after deploying the ``.htaccess`` of academic-meta-tool.xyz and after the
w3id.org entry went live. It needs network access (so it is not part of
``main.py``):

    python py/check_redirects.py                 both sites
    python py/check_redirects.py --site w3id     one site
    python py/check_redirects.py --follow        also fetch every target (must answer 200)
    python py/check_redirects.py --site w3id --base-url http://localhost:8090/amt/   a test server

For each route it asks the server with the Accept headers that matter (a
browser, Turtle, RDF/XML, JSON-LD), without following the redirect, and
compares status and Location with what ``site_redirects.resolve`` expects.
Exit code 1 if anything differs.
"""
from __future__ import annotations

import argparse
import http.client
import sys
import urllib.request
from urllib.parse import urlsplit

try:
    import site_redirects as sr
except ImportError:
    from py import site_redirects as sr

BROWSER = "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8"
ACCEPTS = {"browser": BROWSER, "turtle": "text/turtle", "rdfxml": "application/rdf+xml",
           "jsonld": "application/ld+json"}


def ask(url: str, accept: str) -> tuple[int, str]:
    """One GET without following redirects: (status, Location)."""
    u = urlsplit(url)
    cls = http.client.HTTPSConnection if u.scheme == "https" else http.client.HTTPConnection
    conn = cls(u.netloc, timeout=20)
    conn.request("GET", u.path or "/", headers={"Accept": accept, "User-Agent": "amt-check-redirects"})
    r = conn.getresponse()
    loc = r.getheader("Location") or ""
    conn.close()
    return r.status, loc


def fetch_status(url: str) -> int:
    req = urllib.request.Request(url, headers={"User-Agent": "amt-check-redirects"})
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            return r.status
    except Exception as e:  # report any failure as a status-like number
        return getattr(e, "code", 0)


def main() -> int:
    cfg = sr.load()
    ap = argparse.ArgumentParser(description="Compare the live redirects with deploy/redirects.yaml.")
    ap.add_argument("--site", choices=list(cfg["sites"]), help="check one site only")
    ap.add_argument("--base-url", help="ask this address instead of the one in the YAML (needs --site)")
    ap.add_argument("--follow", action="store_true", help="also fetch every target")
    args = ap.parse_args()
    if args.base_url and not args.site:
        ap.error("--base-url needs --site")
    bad = checked = 0
    fetched: dict[str, int] = {}
    for name, s in cfg["sites"].items():
        if args.site and args.site != name:
            continue
        base = args.base_url or s["base_url"]
        print(f"\n{name}  ({base})")
        for r in s["routes"]:
            variants = list(ACCEPTS.items()) if r.get("vocab") else [("browser", BROWSER)]
            for label, accept in variants:
                exp = sr.resolve(cfg, name, r["path"], accept)
                url = base + r["path"]
                try:
                    got = ask(url, accept)
                except OSError as e:
                    got = (0, f"no answer: {e}")
                ok = got == exp
                if ok and args.follow:
                    fetched.setdefault(exp[1], fetch_status(exp[1]))
                    ok = fetched[exp[1]] == 200
                checked += 1
                bad += not ok
                line = f"  {'ok  ' if ok else 'FAIL'} {url} [{label}] -> {got[0]} {got[1]}"
                print(line if ok else f"{line}   expected {exp[0]} {exp[1]}")
    print(f"\n{checked - bad}/{checked} as expected")
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
