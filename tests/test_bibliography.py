"""data/bibliography.bib: the file is sound, the APA 7 lines are right, the page is current."""
from __future__ import annotations

from pathlib import Path

import site_bib as bib

ROOT = Path(__file__).resolve().parent.parent
DOCS = ROOT / "docs"

SAMPLE = """
@article{a1, author = {Thiery, Florian and Mees, Allard W.}, year = {2025}, title = {A title},
  journal = {Journal of Things}, volume = {12}, number = {1}, pages = {3--9}, doi = {10.1/x}, kind = {paper}}
@inproceedings{b2, author = {Tolle, K. and Gampe, S. and Thiery, Florian}, year = {2026}, title = {Another},
  booktitle = {Proceedings of Things}, pages = {1--18}, url = {https://example.org/p}}
@misc{c3, author = {Jean-Luc Picard}, year = {2027}, title = {A talk}, howpublished = {Conference talk},
  url = {https://example.org/t}, kind = {talk}}
"""


def test_the_real_file_has_no_problems():
    entries = bib.load()
    assert entries and bib.check(entries) == []


def test_parser_reads_fields_and_keeps_the_raw_entry():
    e = bib.parse(SAMPLE)
    assert [x["key"] for x in e] == ["a1", "b2", "c3"]
    assert e[0]["fields"]["pages"] == "3--9" and e[0]["raw"].startswith("@article{a1")


def test_apa_authors_and_initials():
    assert bib.apa_authors("Thiery, Florian and Mees, Allard W.") == "Thiery, F., & Mees, A. W."
    assert bib.apa_authors("Tolle, K. and Gampe, S. and Thiery, Florian") == "Tolle, K., Gampe, S., & Thiery, F."
    assert bib.apa_authors("Jean-Luc Picard") == "Picard, J.-L."


def test_apa_lines():
    a, b, c = (bib.apa(x) for x in bib.parse(SAMPLE))
    assert a.startswith("Thiery, F., &amp; Mees, A. W. (2025). A title. <em>Journal of Things</em>, <em>12</em>(1), 3–9.")
    assert a.endswith('<a href="https://doi.org/10.1/x">https://doi.org/10.1/x</a>')
    assert "In <em>Proceedings of Things</em> (pp. 1–18)." in b
    assert c.startswith("Picard, J.-L. (2027). <em>A talk</em> [Conference talk].")


def test_check_finds_what_would_break_the_page():
    bad = bib.check(bib.parse("@misc{x, author = {A, B}, year = {2020}, title = {T}}\n"
                              "@misc{x, author = {A, B}, year = {2020}, title = {T}, doi = {1/2}, kind = {nope}}"))
    assert any("neither doi nor url" in b for b in bad)
    assert any("used twice" in b for b in bad)
    assert any("unknown kind" in b for b in bad)


def test_page_lists_every_entry_with_its_bibtex_and_is_current():
    entries = bib.load()
    html = (DOCS / "bibliography" / "index.html").read_text(encoding="utf-8").replace("\r\n", "\n")
    assert html == bib.bibliography_page(entries)
    for e in entries:
        assert f'id="{e["key"]}"' in html and "https://doi.org/" + e["fields"]["doi"] in html
    assert (DOCS / "bibliography" / "amt.bib").read_text(encoding="utf-8").replace("\r\n", "\n") == \
        bib.BIB_FILE.read_text(encoding="utf-8").replace("\r\n", "\n")
