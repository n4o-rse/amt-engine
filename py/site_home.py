"""
The start page of the Academic Meta Tool (``docs/index.html``).

English first, German as the second language: both texts are in the page and
``docs/assets/site.js`` shows one of them (``data-lang`` on ``<html>``). Without
JavaScript the visitor sees English. The page is written here, not generated
from data; ``tests/test_site.py`` checks that both languages have the same
structure, so one cannot grow a section the other lacks.

What the page says AMT can and cannot do is taken from the README and from the
code of the engine and of the browser Explorer; when one of them changes, this
text is part of the change.
"""
from __future__ import annotations

from html import escape

try:
    from amt_site import page
except ImportError:
    from py.amt_site import page

SOFTWARE_DOI = "https://doi.org/10.5281/zenodo.23669466"
ARTICLE_DOI = "https://doi.org/10.17175/sb004_004"
DFG_NUMBER = "501836407"

# A worked example from examples/animals.ttl (ex:RCA_classCrossover, Goedel logic).
FLOW = """Rex  --isInstanceOf (1.00)-->  Dog
Dog  --isSubclassOf (0.85)-->  Pet

  inferred:  Rex  --isInstanceOf (0.85)-->  Pet      Goedel logic: min(1.00, 0.85)"""

QUICKSTART = """git clone https://github.com/alpaca-fair-framework/amt-engine
cd amt-engine
pip install -e .
amt-runner examples/animals.ttl"""

TEXT = {
    "en": {
        "tag": "Reasoning with vague knowledge",
        "lead": "AMT models relations that hold only to a degree and derives new relations from them by rules. "
                "It works on RDF graphs, in Python and in the browser.",
        "btn": ["Open the Explorer", "How-To", "Vocabulary", "Data model", "Source code"],
        "ex_h": "An example in three lines",
        "ex_p": "Every relation carries a weight between 0 and 1. A rule says how weights combine along a chain of "
                "relations. AMT applies the rules until nothing new follows, and marks what it inferred.",
        "can_h": "What AMT can do",
        "can": [
            "Weighted relations between concepts, in plain RDF (Turtle).",
            "Rule-based inference to a fixed point: role chains of any length, inverse roles and role subsumption.",
            "Consistency checks: roles that exclude each other, roles that must not point back at their own node.",
            "Six fuzzy logics to combine weights: Gödel, product, Łukasiewicz, Einstein, geometric mean and Hamacher.",
            "Provenance: every inferred relation records the axioms it follows from.",
            "SHACL validation of the input before anything is inferred.",
            "Output as Turtle, Cypher (Neo4j), CSV and an interactive HTML graph, with a Markdown report of each run.",
            "Deterministic results: the same input gives the same bytes, on any machine.",
        ],
        "cannot_h": "What AMT does not do",
        "cannot": [
            "It does not learn weights from data. The weights are degrees you assign, such as confidence or "
            "plausibility; AMT only combines them.",
            "Weights are not probabilities by default. The product logic treats them as independent evidence; "
            "which operator fits is a modelling decision (the vocabulary gives a hint for each).",
            "It is not a full OWL or description-logic reasoner. It knows five kinds of axioms (role chain, inverse, "
            "subsumption, disjoint, self-disjoint) and no class expressions, negation or quantifiers.",
            "It reports inconsistencies; it does not repair them.",
            "The browser Explorer reasons exactly like the engine, but it does not validate the input with SHACL "
            "and writes no report; for that, use the Python engine.",
        ],
        "try_h": "Try it",
        "try_p": "The Explorer runs in your browser: pick an example or load your own Turtle file, look at the graph, switch "
                 "the reasoning on and export the result. For everything else, install the Python engine:",
        "try_btn": "Open the Explorer",
        "hist_h": "Where it comes from",
        "hist_p1": "AMT was developed at <strong>mainzed</strong>, the Mainz Centre for Digitality in the Humanities and "
                   "Cultural Studies, by <strong>i3mainz</strong> (Institute for Spatial Information and Surveying "
                   "Technology, Hochschule Mainz University of Applied Sciences) together with the "
                   "<strong>RGZM</strong> (Römisch-Germanisches Zentralmuseum Mainz, today LEIZA). "
                   "The vocabulary appeared in 2018; the method is described by Unold, Thiery and Mees (2019).",
        "hist_p2": "Today AMT is developed further in <strong>NFDI4Objects</strong>, the consortium for the material "
                   "remains of human history within the National Research Data Infrastructure.",
        "dfg": f"NFDI4Objects is funded by the Deutsche Forschungsgemeinschaft (DFG, German Research Foundation) "
               f"&ndash; project number {DFG_NUMBER}.",
        "name_h": "A name that only works in German",
        "name_p": "<em>AMT</em> stands for <em>Academic Meta Tool</em>. The name only really works in German: an "
                  "<em>Amt</em> is an office or authority, and there, as everyone knows, nothing seems to happen. Our "
                  "AMT does nothing by itself either. It only applies rules, and that is exactly how new knowledge "
                  "arises: semantic reasoning, or symbolic AI.",
        "fam_h": "Part of a family",
        "fam_p": "AMT is part of the Alpaka Research Framework, to which Alligator also belongs. "
                 "The penguin is the Academic Meta Tool.",
        "cite_h": "Cite",
        "cite_p": f'Software: <a href="{SOFTWARE_DOI}">doi:10.5281/zenodo.23669466</a> (all versions). '
                  f'Method: Unold, M., Thiery, F. and Mees, A. (2019), <a href="{ARTICLE_DOI}">Academic Meta Tool. '
                  'Ein Web-Tool zur Modellierung von Vagheit</a>, Zeitschrift f&uuml;r digitale '
                  'Geisteswissenschaften, Sonderband 4. More works that use AMT are listed in the '
                  '<a href="bibliography/">bibliography</a>.',
        "more_h": "More",
    },
    "de": {
        "tag": "Schlussfolgern mit unscharfem Wissen",
        "lead": "AMT modelliert Beziehungen, die nur bis zu einem gewissen Grad gelten, und leitet daraus regelbasiert "
                "neue Beziehungen ab. Es arbeitet auf RDF-Graphen, in Python und im Browser.",
        "btn": ["Explorer öffnen", "Anleitung", "Vokabular", "Datenmodell", "Quellcode"],
        "ex_h": "Ein Beispiel in drei Zeilen",
        "ex_p": "Jede Beziehung trägt ein Gewicht zwischen 0 und 1. Eine Regel legt fest, wie sich Gewichte entlang einer "
                "Kette von Beziehungen verbinden. AMT wendet die Regeln an, bis nichts Neues mehr folgt, und "
                "kennzeichnet, was es abgeleitet hat.",
        "can_h": "Was AMT kann",
        "can": [
            "Gewichtete Beziehungen zwischen Konzepten, in schlichtem RDF (Turtle).",
            "Regelbasiertes Ableiten bis zum Fixpunkt: Rollenketten beliebiger Länge, inverse Rollen und "
            "Rollen-Subsumtion.",
            "Konsistenzprüfungen: Rollen, die sich ausschließen, und Rollen, die nicht auf den eigenen Knoten "
            "zurückzeigen dürfen.",
            "Sechs Fuzzy-Logiken zum Verbinden der Gewichte: Gödel, Produkt, Łukasiewicz, Einstein, geometrisches "
            "Mittel und Hamacher.",
            "Herkunft: Jede abgeleitete Beziehung nennt die Axiome, aus denen sie folgt.",
            "SHACL-Prüfung der Eingabe, bevor etwas abgeleitet wird.",
            "Ausgabe als Turtle, Cypher (Neo4j), CSV und interaktiver HTML-Graph, dazu ein Markdown-Bericht je Lauf.",
            "Reproduzierbare Ergebnisse: gleiche Eingabe, gleiche Bytes, auf jedem Rechner.",
        ],
        "cannot_h": "Was AMT nicht kann",
        "cannot": [
            "Es lernt keine Gewichte aus Daten. Die Gewichte sind Grade, die Sie vergeben, etwa Sicherheit oder "
            "Plausibilität; AMT verbindet sie nur.",
            "Gewichte sind standardmäßig keine Wahrscheinlichkeiten. Die Produkt-Logik behandelt sie als "
            "unabhängige Belege; welcher Operator passt, ist eine Modellierungsentscheidung (das Vokabular gibt "
            "je einen Hinweis).",
            "Es ist kein vollständiger OWL- oder Beschreibungslogik-Reasoner. Es kennt fünf Axiomarten "
            "(Rollenkette, Inverse, Subsumtion, disjunkt, selbst-disjunkt) und keine Klassenausdrücke, Negation "
            "oder Quantoren.",
            "Es meldet Widersprüche; es behebt sie nicht.",
            "Der Explorer im Browser schließt genau wie die Engine, prüft die Eingabe aber nicht mit SHACL und "
            "schreibt keinen Bericht; dafür nehmen Sie die Python-Engine.",
        ],
        "try_h": "Ausprobieren",
        "try_p": "Der Explorer läuft in Ihrem Browser: ein Beispiel wählen oder eine eigene Turtle-Datei laden, den Graphen "
                 "ansehen, das Schlussfolgern "
                 "einschalten und das Ergebnis exportieren. Für alles Weitere installieren Sie die Python-Engine:",
        "try_btn": "Explorer öffnen",
        "hist_h": "Woher es kommt",
        "hist_p1": "AMT wurde am <strong>mainzed</strong>, dem Mainzer Zentrum für Digitalität in den Geistes- und "
                   "Kulturwissenschaften, entwickelt: vom <strong>i3mainz</strong> (Institut für Raumbezogene "
                   "Informations- und Messtechnik der Hochschule Mainz) gemeinsam mit dem <strong>RGZM</strong> "
                   "(Römisch-Germanisches Zentralmuseum Mainz, heute LEIZA). Das Vokabular erschien 2018; die "
                   "Methode beschreiben Unold, Thiery und Mees (2019).",
        "hist_p2": "Heute wird AMT in <strong>NFDI4Objects</strong> weiterentwickelt, dem Konsortium für die "
                   "materiellen Hinterlassenschaften der Menschheitsgeschichte in der Nationalen "
                   "Forschungsdateninfrastruktur.",
        "dfg": f"NFDI4Objects wird von der Deutschen Forschungsgemeinschaft (DFG) gefördert &ndash; "
               f"Projektnummer {DFG_NUMBER}.",
        "name_h": "Ein Name, der nur auf Deutsch funktioniert",
        "name_p": "<em>AMT</em> steht für <em>Academic Meta Tool</em>. Der Name funktioniert eigentlich nur auf "
                  "Deutsch: Ein <em>Amt</em> ist eine Behörde, und dort passiert bekanntlich nichts. Unser AMT tut "
                  "selbst auch nichts. Es wendet nur Regeln an, und genau dadurch entsteht neues Wissen: "
                  "semantisches Schlussfolgern, also symbolische KI.",
        "fam_h": "Teil einer Familie",
        "fam_p": "AMT ist Teil des Alpaka Research Frameworks, zu dem auch Alligator gehört. "
                 "Der Pinguin ist das Academic Meta Tool.",
        "cite_h": "Zitieren",
        "cite_p": f'Software: <a href="{SOFTWARE_DOI}">doi:10.5281/zenodo.23669466</a> (alle Versionen). '
                  f'Methode: Unold, M., Thiery, F. und Mees, A. (2019), <a href="{ARTICLE_DOI}">Academic Meta Tool. '
                  'Ein Web-Tool zur Modellierung von Vagheit</a>, Zeitschrift f&uuml;r digitale '
                  'Geisteswissenschaften, Sonderband 4. Weitere Arbeiten, die AMT nutzen, stehen in der '
                  '<a href="bibliography/">Bibliografie</a>.',
        "more_h": "Mehr",
    },
}

LINKS = ["explorer/", "howto/", "vocab/", "ontology/", "https://github.com/alpaca-fair-framework/amt-engine"]


def _block(lang: str) -> str:
    t = TEXT[lang]
    li = lambda items: "".join(f"<li>{escape(x)}</li>" for x in items)
    btns = "".join(
        f'<a class="btn{" primary" if i == 0 else ""}" href="{href}">{escape(label)}</a>'
        for i, (label, href) in enumerate(zip(t["btn"], LINKS))
    )
    return f"""<div data-l="{lang}" lang="{lang}">
<section class="hero">
<img class="mascot" src="assets/img/amt-penguin.png" alt="The AMT penguin with a book under its wing" width="210">
<h1>Academic Meta Tool</h1>
<p class="tag">{escape(t["tag"])}</p>
<p class="lead">{escape(t["lead"])}</p>
<div class="btns">{btns}</div>
</section>

<h2>{escape(t["ex_h"])}</h2>
<p>{escape(t["ex_p"])}</p>
<pre class="flow"><code>{escape(FLOW)}</code></pre>

<div class="cols">
<div class="term"><h3>{escape(t["can_h"])}</h3><ul>{li(t["can"])}</ul></div>
<div class="term no"><h3>{escape(t["cannot_h"])}</h3><ul>{li(t["cannot"])}</ul></div>
</div>

<h2>{escape(t["try_h"])}</h2>
<p>{escape(t["try_p"])}</p>
<pre><code>{escape(QUICKSTART)}</code></pre>
<div class="btns"><a class="btn primary" href="explorer/">{escape(t["try_btn"])}</a></div>

<h2>{escape(t["hist_h"])}</h2>
<p>{t["hist_p1"]}</p>
<p>{t["hist_p2"]}</p>
<p class="note">{t["dfg"]}</p>

<h2>{escape(t["name_h"])}</h2>
<p>{t["name_p"]}</p>

<h2>{escape(t["fam_h"])}</h2>
<p>{escape(t["fam_p"])}</p>
<div class="family">
<figure class="me"><img src="assets/img/amt-penguin.png" alt="" loading="lazy"><figcaption>AMT</figcaption></figure>
<figure><img src="assets/img/alpaka.png" alt="" loading="lazy"><figcaption>Alpaka</figcaption></figure>
<figure><img src="assets/img/alligator.png" alt="" loading="lazy"><figcaption>Alligator</figcaption></figure>
</div>

<h2>{escape(t["cite_h"])}</h2>
<p>{t["cite_p"]}</p>
</div>"""


def home_page() -> str:
    body = _block("en") + "\n" + _block("de")
    return page(title="Academic Meta Tool", body=body, depth=0, current="home", lang_switch=True,
                description="Reasoning with vague knowledge: weighted relations and rules that derive new relations. "
                            "Developed at mainzed, continued in NFDI4Objects.")
