# PRIMER – amt-engine

Arbeitsplan für das Repo `amt-engine` (Academic Meta Tool, Python-Reasoner). Wird zu Beginn jedes Chats komplett hochgeladen und am Ende zurückgeschrieben. Teil A gilt immer, Teil B ist die Übersicht, Teil C sind die Schritte, Teil D sind offene Punkte.

---

## Teil A – Immer gültig

### A1 Ausgangslage

| Was | Wo | Rolle |
|---|---|---|
| Bibliothek und CLI | `amt/` | installierbares Paket, Befehle `amt` und `amt-runner` (Version 0.3.0) |
| Ontologie | `ontology/` | `amt.ttl`, `amt-shapes.ttl`, Beispiele, `validate_examples.py` |
| Beispiele | `examples/` | Eingaben; `*.ttl` werden nach `docs/data/` gespiegelt |
| Tests | `tests/test_amt.py` | 62 Tests |
| Webviewer | `docs/` | JavaScript-AMT für GitHub Pages |
| Dev-Pipeline | `main.py`, `py/` | Wartungsschritte (seit S1), kein Teil des Pakets |
| Begleit-Repo | `amt-runner` | Wrapper `run_amt.py`, klont diese Engine; eigenes Primer-Thema (S2) |

**Befunde** (alle am 2026-10-26 geprüft, Stand `a50822c`):

- Das README verwies auf `docs/architecture.mmd`; die Datei liegt in `amt/architecture.mmd`. Das Layout-Diagramm im README führte denselben Fehler. Beides korrigiert in S1.
- `docs/data/subsumption-demo.ttl` fehlte. Der Workflow `sync-examples-to-docs.yml` startet nur bei einem Push, der `examples/**` berührt; die Datei kam mit Commit `03eb093` nach `examples/`. Warum der Sync nicht gelaufen ist, ist offen (die Actions-Läufe waren nicht einsehbar). `python main.py --only docs-sync` legt sie an.
- Zwei Läufe der Pipeline auf `animals.ttl` und `subsumption-demo.ttl` unter `PYTHONHASHSEED=1` und `=2`: fünf der sechs Ausgabedateien sind byte-identisch, nur `*.report.md` unterscheidet sich (Start- und Endzeit). Die Reihenfolge-Korrektur aus 0.3.0 hält also.
- `pytest` meldete 62 grüne Tests und rund 83 700 Warnungen (rdflib-Deprecation; die Zahl schwankt leicht zwischen Läufen); die Warnungen verdeckten jede andere Meldung. Ursache in S7 geklärt (D3).
- `.gitignore` schließt `dist/` aus (setuptools-Ausgabe). Das Primer-Muster legt Produkte sonst in `dist/` ab; hier geht das nicht, siehe A4.
- Die Historie hatte 30 Commits und keine Tags. Die Versionen standen nur in `pyproject.toml`: 0.1.0 (2026-04-28), 0.2.0 (2026-05-05), 0.3.0 (2026-08-29). Seit S5 tragen die Commits `3357cde`, `5cc2fbf` und `03eb093` die Tags `v0.1.0` bis `v0.3.0`.
- Commit `db1db2d` (2026-05-04) führt den Verlauf von `amt-explore` in dieses Repo zusammen. Der Webviewer in `docs/` stammt von dort. Die Adresse `https://github.com/n4o-rse/amt-explore` leitet am 2026-10-26 auf dieses Repo um; der Webviewer läuft als „AMT Explorer“ unter `https://n4o-rse.github.io/amt-engine/`.
- Windows-Lauf von `python main.py` (2026-10-26, `C:\git\amt-engine`): alle sechs Schritte `ok`, 62 Tests grün in 16,4 s, Gesamtlauf 38,1 s. Der Determinismus-Test besteht auch dort. Die Warnungszahl im Testlauf liegt mit 15 006 weit unter dem Linux-Wert (rdflib- und Python-Version, siehe D3).
- `docs-sync` meldete auf Windows fünf Dateien als `updated`, obwohl die Blobs in `examples/` und `docs/data/` identisch sind und überall nur LF enthalten (geprüft an `9a0e8b7`). Ursache: `core.autocrlf` macht im Working Tree CRLF daraus; der Byte-Vergleich sah Unterschiede, wo keine sind. Behoben in S1a.
- `examples/skos-mapping-example.ttl` meldet beim Konsistenzcheck zwei Verletzungen (`exactMatch` und `questionableMatch` zum selben Ziel; Selbstschleife über `questionableMatch`). Das ist als Demo gewollt (A4). Der Runner beendet sich trotzdem mit Exit-Code 0, deshalb bleibt der Schritt `examples` auf `ok`.
- Rückmeldung aus der Praxis (Karsten, AFE-Münzen, 2026-10-27): Eine per SPARQL CONSTRUCT erzeugte Datei bestand die Validierung, der Lauf endete aber mit `AssertionError: non existent node 'http://nomisma.org/id/vespasian'` in `amt/viz.py`. Ursache: nur die Münzen hatten `amt:instanceOf`, die Ziele der Kanten (`nm:vespasian` usw.) nicht; `load_amt` lädt nur Knoten mit `amt:instanceOf`, die Kanten blieben ohne Endknoten, `pyvis.add_edge` bricht dann ab (geprüft mit `AFE_all_cases_asAMT.ttl`: 4 Knoten, 7 Kanten, 7 Kantenenden ohne Knoten). Zweites Fehlerbild: `amt:instanceOf amt:Concept` löst „Each Concept must have at least one rdfs:label“ aus (der Bereich von `amt:instanceOf` ist `amt:Concept`, also zählt jedes Objekt als Konzept), und die Meldung nannte den Knoten nicht. `lado:hasAMT` stört nicht: die Engine liest Kanten nur über `amt:weight`.
- `pyproject.toml` nannte als Autor „AMT contributors"; `LICENSE` nannte Florian Thiery | LEIZA | NFDI4Objects; `docs/index.htm` nennt Thiery und Unold (Software) sowie Thiery und Mees (Datenkonzept). Geklärt in S3 (A4).
- Umzug der Repos (2026-10-30, Stand `987dd8d`): `amt-engine` und `amt-runner` liegen jetzt unter `https://github.com/alpaca-fair-framework/`. Im Quelltext stehen noch 137 Zeilen mit `n4o-rse` (102 in der Engine, 35 im Runner), in fünf Mustern: `n4o-rse/amt-engine`, `n4o-rse/amt-runner`, `n4o-rse/amt-explore`, `n4o-rse.github.io` (Adresse der Pages) und der Organisationsname allein. Betroffen sind Quellen (`py/site_*.py`, `amt/runner.py`), `CITATION.cff`, `README.md`, `deploy/redirects.yaml` samt erzeugten `.htaccess`, die Beispiel-TTLs, Tests und die erzeugten Seiten unter `docs/`; im Runner stehen `AMT_REPO_URL`, `EXPLORER_URL` und `HOWTO_URL` in `run_amt.py`. Gezählt mit `grep` ohne `.git` und `docs/vendor/`. Nicht geprüft: ob die alte Pages-Adresse weiter antwortet und ob die Zenodo-Anbindung an der neuen Organisation hängt.
- Das Quadrupel in der Engine (2026-10-30): Eine Aussage ist ein reifizierter Knoten mit `rdf:subject`, `rdf:predicate`, `rdf:object` und `amt:weight`. `core.load_amt` liest jeden Knoten mit `amt:weight` in ein Kanten-Dict mit den Schlüsseln `role`, `from`, `to`, `weight`, `inferred`, `provenance`. Dieselben sechs Schlüssel laufen durch `reasoning.py` (`_add_or_strengthen_edge` legt abgeleitete Kanten nur mit ihnen an), `subsumption.py`, `export.py` (Turtle, Cypher, `edges.csv`), `viz.py`, den JS-Port `docs/js/amt-reasoner.js` und `amt:WeightShape`. Weitere Felder gibt es nirgends; das Wort „Quadrupel“ steht nur in Kommentaren von `amt.ttl` und `amt-shapes.ttl`.
- FW-Ontologie (2026-10-30, `caa-datadragons/FW_Ontology`, Stand `15ae05f`): Namensraum `http://w3id.org/fw_ontology/` (mit `http`), Präfix `fw:`. Für eine Aussage gibt es `fw:hasDegreeOfConnection` (`owl:equivalentProperty amt:weight`), `fw:hasType` (Wert ist ein Individuum von `fw:FW_Type`: `fw:Vagueness`, `fw:Uncertainty`, `fw:FuzzinessWobbliness`; die beiden ersten haben `skos:broader fw:FuzzinessWobbliness`), `fw:hasMethod` (Wert ist ein Individuum von `fw:Method`, z. B. `fw:EqualShareRule`) und optional `fw:derivedFrom` auf `fw:Evidence` (`fw:TextEvidence` mit `fw:sourceString`). `fw:implementedBy` ist definiert, für `fw:EqualShareRule` aber noch nicht gesetzt. Die sechs AMT-Logiken als `fw:PropagationMethod` stehen dort nur als Vorschlag in `data/amt-alignment.ttl`, mit dem Vermerk, dass sie nach `amt.ttl` gehören. Die Zuordnung der Muster `?`, OR und AND zu den Typen liegt im Mini-AMT-Repo (`weights.py`), nicht hier.
- Zwei Lücken im heutigen Reasoning, die der Hextupel-Schritt klären muss (2026-10-30): (1) `InverseAxiom` und `SubsumptionAxiom` legen abgeleitete Kanten über `_add_or_strengthen_edge` an, haben aber keine Logik; für `fw:hasMethod` gibt es dort keine naheliegende Methode. (2) Wird eine Kante auf mehreren Wegen abgeleitet, gilt das Maximum der Gewichte und die Herkunftslisten werden vereinigt (Kopf von `reasoning.py`); welcher Weg dann Typ und Methode liefert, ist offen. Beides in D14.
- Die Turtle-Ausgabe besteht die eigene Validierung nicht (2026-10-30): `export.py` schreibt `amt:weight` als `"1.000000"^^xsd:double`, `amt:WeightShape` verlangt `xsd:decimal`. Lauf auf `examples/animals.ttl` (Linux, Python 3.13, rdflib und pyshacl in den aktuellen pip-Versionen): die Eingabe ist konform, `animals.reasoned.ttl` hat 152 Verstöße, alle mit derselben Meldung (46 behauptete plus 106 abgeleitete Kanten). Die Engine liest die Datei trotzdem, weil `core.load_amt` `float()` nimmt; nur die Validierung der eigenen Ausgabe scheitert. Das trifft den Roundtrip (Ausgabe wieder einlesen), den die AFE-Arbeit braucht. Beschlussvorschlag in D15.


### A2 Zielbild

```
amt/  ontology/  examples/  tests/  pyproject.toml  CHANGELOG.md  CITATION.cff
        │
        ▼
python main.py
  meta ─► ontology ─► docs-sync ─► site ─► tests ─► examples ─► determinism
        │
        ▼
build/pipeline_report.txt        docs/data/*.ttl (Spiegel von examples/)
                                 docs/index.html, docs/vocab, docs/ontology, docs/assets (erzeugt aus ontology/amt.ttl)
```

Eigenschaften, die das Repo haben muss:

1. `python main.py --strict` endet mit Exit-Code 0 auf einem sauberen Checkout.
2. Zweimal `python main.py`, danach `git status` sauber (bei einem Repo, in dem `docs/data/` schon synchron ist).
3. Version in `pyproject.toml`, `amt/__init__.py`, `CITATION.cff`, `CHANGELOG.md` und `py/amt_dev_utils.py` stimmt überein; sonst bricht `meta` ab.
4. Jede ausgelieferte Änderung steht im `CHANGELOG.md` unter `[Unreleased]` oder unter der Version.
5. Die Produktbefehle `amt` und `amt-runner` verhalten sich wie vor dem Primer.

### A3 Querschnittsregeln

- Eingaben (`examples/`, `ontology/`) verändert kein Skript. Was ein Schritt schreibt, landet in `build/` oder, beim Spiegel, in `docs/data/`.
- Keine Uhr in Repo-Inhalten: `RELEASE` und `RELEASE_DATE` in `py/amt_dev_utils.py`. Ausgenommen sind Laufzeit-Reports der Engine, siehe A4.
- Zweimal laufen lassen, `git status` bleibt beim zweiten Mal sauber.
- Kein Netzwerkzugriff in `main.py`. Alle Schritte laufen offline.
- Der Determinismus-Test läuft unter verschiedenen `PYTHONHASHSEED`-Werten; zwei Läufe mit demselben Seed würden den Fehler aus 0.3.0 nicht finden.
- Code, Kommentare, README, CHANGELOG, CITATION.cff: British English. `PRIMER.md` ist Deutsch.
- Befehle für Windows `cmd`, je Zeile ein Befehl, keine Fortsetzungszeichen.
- Ein Thema pro Chat, ein Repo pro Chat.
- Änderungen an `amt/` oder `ontology/` brauchen einen Eintrag im `CHANGELOG.md` und, wenn sie Verhalten ändern, einen Test.
- `requirements.txt` ändert nur, wer den Runner mitdenkt: `amt-runner` installiert daraus.
- `PATCH-README.md` begleitet ein Patch-ZIP und gehört nicht ins Repo; sie steht seit `b42b27b` in `.gitignore`.
- Pro Repo genau eine `requirements.txt`, ohne `requirements-dev.txt`; Entwicklungspakete stehen in derselben Datei, mit Kommentar. Seit S6 gilt das auch hier.

### A4 Beschlusslage

| Frage | Beschluss | seit |
|---|---|---|
| Reihenfolge der Repos | `amt-engine` zuerst, danach `amt-runner` (eigener Chat) | 2026-10-26 |
| Umgang mit dem Orchestrator-Vertrag | `main.py` ist ein dünner Dev-Orchestrator; `amt` und `amt-runner` bleiben die Produkt-CLIs und werden nicht umgebaut | 2026-10-26 |
| Uhr im Output | Laufzeit-Ausgaben behalten ihre Zeitstempel (`*.report.md`, `out/run-<Zeitstempel>` im Runner); die Regel „keine Uhr" gilt für Repo-Inhalte | 2026-10-26 |
| CHANGELOG | Keep a Changelog, rückwirkend aus der Historie rekonstruiert (0.1.0 bis 0.3.0); Datum = Commit, der die Versionsnummer gesetzt hat; keine Tags vorhanden | 2026-10-26 |
| Ort des Pipeline-Reports | `build/pipeline_report.txt`, nicht `dist/`: `dist/` ist hier setuptools-Ausgabe und ignoriert (Abweichung vom Muster, mit Grund) | 2026-10-26 |
| Verhalten von `docs-sync` | kopiert immer; mit `--strict` schlägt der Schritt fehl, wenn etwas kopiert werden musste (Drift-Prüfung für CI) | 2026-10-26 |
| Zeilenenden in `docs-sync` | Vergleich mit normalisierten Zeilenenden (CRLF = LF); kein `.gitattributes` | 2026-10-26 |
| `skos-mapping-example.ttl` | die zwei Konsistenzverletzungen sind gewollt (Demo für `DisjointAxiom` und `SelfDisjointAxiom`) | 2026-10-26 |
| Exit-Code des Runners bei Konsistenzverletzungen | bleibt 0; eine Änderung wäre ein Verhaltenswechsel der Produkt-CLI und braucht einen eigenen Schritt samt Version | 2026-10-26 |
| Anzahl der requirements-Dateien | familienweit genau eine `requirements.txt` pro Repo; `amt-engine` hat `requirements-dev.txt` in S6 eingefasst (`pytest` steht mit Kommentar in `requirements.txt`) | 2026-10-26 |
| `pytest` beim Runner | darf mitkommen: der Runner installiert die `requirements.txt` der Engine samt `pytest`; kein zweiter Satz Laufzeitpakete | 2026-10-26 |
| Versionen der GitHub Actions | Hauptversionen mit Node 24: `checkout@v5`, `setup-python@v6`, `upload-artifact@v6`; Node 24 geprüft an `action.yml` der Tags (`upload-artifact@v5` läuft noch auf Node 20, ab v6 Node 24); bei der nächsten Node-Warnung erneut prüfen | 2026-10-26 |
| Standard-Ref des Runners | `amt-runner` zeigt weiter auf `main`; ein Pin auf Tags kommt erst nach S5 | 2026-10-26 |
| Autoren in `CITATION.cff` und `pyproject.toml` | Florian Thiery (ORCID 0000-0002-3246-3531) und Allard W. Mees (ORCID 0000-0002-7634-5342), beide LEIZA; ersetzt den Vorschlag „nur Thiery“ | 2026-10-26 |
| Rechteinhaber in `LICENSE` | „Florian Thiery \| LEIZA \| Research Squirrel Engineers Network“, in beiden Repos gleich; `docs/LICENSE` und `docs/js/LICENSE` bleiben unverändert (Dritt- und Altbestand) | 2026-10-26 |
| CI-Matrix | Ubuntu und Windows, Python 3.10 und 3.13; Auslöser Push auf `main`, Pull Request und manuell; `python main.py --strict`; Report als Artefakt | 2026-10-26 |
| Rolle von Unold | kein Autor von AMT.engine; das ursprüngliche Academic Meta Tool (Unold, Thiery, 2017) steht unter `references` in `CITATION.cff`, ohne erfundene DOI | 2026-10-26 |
| Bedeutung von `RELEASE_DATE` | Datum des Commits, der die Version gesetzt hat (0.3.0: 2026-08-29, 0.3.1: 2026-10-26) | 2026-10-26 |
| Tags und Releases | `v0.1.0` bis `v0.3.0` als annotierte Tags auf den Commits aus dem CHANGELOG, ohne GitHub-Release; `v0.3.1` ist das erste Release (Version 0.3.1: keine Verhaltensänderung, nur Metadaten, Tooling, CI) | 2026-10-26 |
| Verhältnis zu `amt-explore` | kein eigenständiges zweites Repo: die Adresse leitet auf `amt-engine` um (Befund 2026-10-26, nicht aus der Historie belegt); `docs/` in diesem Repo ist maßgeblich | 2026-10-26 |
| Standard-Ref des Runners (Tags) | bleibt `main`; Pin auf `v0.3.1` ist ein Beispiel in der README des Runners, kein Standard | 2026-10-26 |
| Reihenfolge der SHACL-Verstöße | sortiert nach Knoten, Pfad und Meldung (`amt/validation.py`, `ontology/validate_examples.py`); die Menge der Verstöße ändert sich nicht | 2026-10-26 |
| Rdflib-Warnungen im Testlauf | zwei Deprecation-Meldungen, die pyshacl auslöst, sind in `pyproject.toml` gefiltert; alle anderen Warnungen bleiben sichtbar | 2026-10-26 |
| DOI | Concept-DOI `10.5281/zenodo.23669466` steht in `CITATION.cff` und README; Version 0.3.1 trägt `10.5281/zenodo.23669467` | 2026-10-26 |
| Vokabular und Ontologie im Repo | `docs/vocab/` und `docs/ontology/` sind maßgeblich und werden von `python main.py` (Schritt `site`) aus `ontology/amt.ttl` erzeugt: Seite, `amt.ttl`, `amt.rdf`, `amt.jsonld`; die Namensraum-IRI `http://academic-meta-tool.xyz/vocab#` bleibt unverändert; Befund D2: `amt.ttl` ist eine Obermenge der Fassung von 2018, nichts ging verloren | 2026-10-26 |
| Abbildungen der Seiten | werden aus Code gezeichnet (`py/site_figures.py`), SVG und PNG (3-fach); die Übersicht entsteht aus `amt.ttl`, nur die Positionen sind festgelegt; SVG wird byteweise geprüft, PNG nicht (hängt von Pillow ab) und nur bei geändertem SVG neu gezeichnet (`docs/assets/figures.json`); die alten Grafiken vom FTP werden nicht übernommen | 2026-10-26 |
| Pillow | Entwicklungs-Abhängigkeit (`requirements.txt`, Extra `dev`), nur für die PNG-Abbildungen; `Pillow>=10.1` wegen `ImageFont.load_default(size)` | 2026-10-26 |
| Lizenz und Autoren der Vokabular-Seite | CC BY 4.0 und die Autoren Florian Thiery und Martin Unold, wie auf den Seiten von 2018 veröffentlicht; Quelle: Unold, Thiery, Mees (2019), ZfdG Sonderband 4, DOI 10.17175/sb004_004 | 2026-10-26 |
| Hell/Dunkel | alle Seiten folgen dem System und haben einen Umschalter (`docs/assets/site.js`); Abbildungen sind eingebettetes SVG und folgen über CSS-Variablen | 2026-10-26 |
| Geplante Reihenfolge bis 0.4.0 | S9 Vokabular/Ontologie, S10 Startseite (Englisch und Deutsch, Explorer nach `/explorer/`, DFG-Verweis Projektnummer 501836407), S11 Playground, S12 w3id und Umleitung des FTP, S13 D6 und Release 0.4.0 | 2026-10-26 |
| Playground | maßgeblich ist `leiza-rse/amt-playground` (Original zum ZfdG-Artikel); es muss mit dem neuen AMT wieder interaktiv Graphen erzeugen; eigener Schritt S11 | 2026-10-26 |
| Playground-Ziel | in der Engine heißt die Anwendung weiter **Explorer** (`/explorer/`, kein eigenes `/playground/`), mit allen Beispielen aus `docs/data/` und „TTL laden“; `leiza-rse/amt-playground` bleibt der **Playground** mit nur dem Personen-Interessen-Netzwerk, ohne Triplestore und ohne Datei laden; beide nutzen denselben JS-Reasoner (Engine ist Quelle, der Playground bekommt eine Kopie) | 2026-10-26 |
| JS-Reasoner | `docs/js/amt-reasoner.js` ist ein Port von `amt/reasoning.py` und `amt/logic.py` (Entailment-Lesart, ohne `minimal`); `tests/test_js_reasoner.py` vergleicht beide auf allen Beispielen (Node nötig, sonst übersprungen); Änderungen an der Python-Logik ziehen den JS-Port nach | 2026-10-26 |
| Startseite | `docs/index.html` aus `py/site_home.py`; Englisch bevorzugt, Deutsch umschaltbar, Hell/Dunkel; Explorer unter `/explorer/`, `docs/index.htm` leitet weiter; DFG-Projektnummer 501836407 bestätigt | 2026-10-26 |
| Release 0.5.0 | mit S18 (Patch 18a): Engine 0.5.0, Runner 0.4.0; Anlass sind Diagnose, `--check-only` und die How-To-Sektion (S16, S17); Tag, Release und Zenodo danach durch den Autor, die Versions-DOIs kommen als Patch 18c | 2026-10-27 |
| Release 0.4.0 | mit S13 (Patch 13a); die ungereleasten Änderungen aus S7 bis S14 gehören dazu; Tag, Release und Zenodo danach durch den Autor | 2026-10-27 |
| Zenodo | GitHub-Zenodo-Anbindung ist für beide Repos eingeschaltet; jedes GitHub-Release erzeugt eine Version mit DOI, ein bloßer Tag nicht; deshalb keine Releases für alte Versionen | 2026-10-26 |
| Öffentliche w3id-Adresse | `https://w3id.org/amt/`, ohne `ids/`: der Ordner `ids/amt/` im Repo `perma-id/w3id.org` ist nur der Ablageort, `RewriteBase` ist `/amt/` (Erfahrung des Autors; am 2026-10-27 korrigiert, S12 hatte `/ids/amt/`) | 2026-10-27 |
| w3id-Pull-Request | wir warten nicht auf den Merge; passt etwas nicht, gibt es einen Hotfix; Header der `.htaccess` (Adressliste, Namensraum, Kontakt) wird aus `deploy/redirects.yaml` erzeugt | 2026-10-27 |
| Bibliografie | Quelle `data/bibliography.bib` (BibTeX, ein Eintrag je Werk, Feld `kind`: paper, talk, software, dataset, other); die Seite `docs/bibliography/` zeigt APA 7 (alphabetisch nach Erstautorin, dann Jahr) mit dem BibTeX je Eintrag und `amt.bib` zum Laden; eigener Parser und Formatter in `py/site_bib.py`, keine zusätzliche Abhängigkeit | 2026-10-27 |
| Zitieren | `CITATION.cff`: `preferred-citation` ist der ZfdG-Artikel (Unold, Thiery, Mees 2019); die Software wird über die DOI zitiert | 2026-10-27 |
| Keine Bibliotheken von CDNs | die Bibliotheken des Explorers (n3, vis, jQuery, jQuery UI, Materialize, Material Icons) liegen unverändert in `docs/vendor/` (Versionen und Lizenzen in `docs/vendor/README.md`); der pyvis-Export bettet vis ein und entfernt den Bootstrap-Verweis (Option `cdn_resources`, Standard `in_line`); `tests/test_offline.py` prüft, dass keine Seite etwas von fremden Servern lädt | 2026-10-27 |
| Rechte, Impressum | Rechte an Logos und Maskottchen sind geklärt (Autor); Impressum und Datenschutzerklärung sind für diese Seiten nicht nötig (Autor) | 2026-10-27 |
| Texte der Startseite | Namensgeschichte in der Fassung B („AMT steht für Academic Meta Tool. Der Name funktioniert eigentlich nur auf Deutsch …“); Familiensatz ohne Links, weil Alpaka und Alligator noch entstehen bzw. überarbeitet werden | 2026-10-27 |
| Version des Runners | 0.3.0, zusammen mit der Engine 0.4.0 (schlankere Abhängigkeiten, Explorer-Hinweis) | 2026-10-27 |
| Diagnose statt Absturz | Kantenenden ohne `amt:instanceOf` sind ein Befund `AMT-E101` (mit IRI und Zeilen zum Einfügen), kein Abbruch; `viz.py` zeichnet solche Enden als graue Platzhalter; Modul `amt/diagnostics.py` (nicht `diagnose.py`: der Name würde in `amt/__init__.py` von der Funktion `diagnose` verdeckt) | 2026-10-27 |
| Exit-Codes des Runners | 0 fertig, 1 Validierung oder `--strict` gescheitert, 2 Eingabe fehlt, 3 unerwarteter Fehler (`--debug` zeigt den Traceback); Diagnose-Fehler ändern den Exit-Code nur mit `--strict`; D6 bleibt unverändert (Konsistenzverletzungen: 0) | 2026-10-27 |
| `--check-only` | Validieren, laden, diagnostizieren, nichts schreiben; auch im Wrapper `amt-runner/run_amt.py` (kein Ausgabeordner, kein `latest`) | 2026-10-27 |
| How-To-Sektion | `docs/howto/` (Übersicht, „bauen“, „prüfen“) aus `py/site_howto.py`; Beispiele und das SPARQL-Rezept stehen im Modul und werden von `tests/test_howto.py` ausgeführt; jeder Code von `amt/diagnostics.py` hat einen Eintrag mit Anker auf der Seite „prüfen“; weitere Unterseiten kommen als Einträge in `PAGES` | 2026-10-27 |
| Hextupel: Begriff | Die AMT-Aussage ist heute ein Quadrupel (Subjekt, Rolle, Objekt, `amt:weight`). Das Hextupel ergänzt `fw:hasType` und `fw:hasMethod` aus `caa-datadragons/FW_Ontology` (Namensraum `http://w3id.org/fw_ontology/`, Präfix `fw:`). Die früher gedachten Namen `amt:type` und `amt:method` entfallen | 2026-10-30 |
| Hextupel: Standard „vage“ | Jede AMT-Aussage ist, wenn nichts anderes angegeben ist, eine Vagheitsaussage; der wirksame Typ ist dann `fw:Vagueness`. Das gilt auch bei Gewicht 1.0 | 2026-10-30 |
| Hextupel: Standard nur implizit | Die Engine nimmt `fw:Vagueness` an und schreibt `fw:hasType` in die Turtle-Ausgabe nur, wenn es in der Eingabe stand oder wenn eine abgeleitete Kante vom Standard abweicht. CSV, Cypher und Graph zeigen den wirksamen Typ. Eine Datei ohne Typ bleibt in der Ausgabe ohne Typ (verlustfreier Roundtrip) | 2026-10-30 |
| Hextupel: Umsetzung des Standards | Im Kanten-Dict ist `type` ein IRI-String oder `None` (= Standard); `effective_type(edge)` liefert den wirksamen Typ. Eine abgeleitete Kante, deren Typ der Standard ist, bekommt `None`; ein ausdrücklich gesetztes `fw:Vagueness` an einer behaupteten Kante bleibt erhalten (Umsetzungsdetail, in S20 mit bestätigt) | 2026-10-30 |
| Hextupel: Gewichts-Property | Eingabe: `amt:weight` und `fw:hasDegreeOfConnection` werden beide gelesen; Ausgabe: `amt:weight`. Die Äquivalenz steht in der FW-Ontologie (`owl:equivalentProperty`) | 2026-10-30 |
| Hextupel: widersprüchliche Gewichte | Trägt eine Aussage beide Properties mit verschiedenen Werten, meldet die Diagnose einen Fehler (`AMT-E104`) und die Engine nimmt `amt:weight` | 2026-10-30 |
| Hextupel: Pflicht | `fw:hasType` und `fw:hasMethod` sind optional. Ein Quadrupel ohne beide bleibt gültig und läuft wie in 0.5.0. Auffälligkeiten sind Diagnose-Befunde, weder SHACL-Verstöße noch Abbrüche | 2026-10-30 |
| Hextupel: Diagnose-Codes | `AMT-W205` (`fw:hasType` nennt keines der drei Individuen `fw:Vagueness`, `fw:Uncertainty`, `fw:FuzzinessWobbliness`) und `AMT-N303` (Typ ohne Methode); zusammen mit `AMT-E104` je ein Eintrag auf der Seite „prüfen“. Eine Methode ohne Typ ist kein Befund, weil der Standard gilt | 2026-10-30 |
| Hextupel: abgeleitete Kanten | Methode: bei `RoleChainAxiom` die Logik der Achse (z. B. `amt:GoedelLogic`). Typ: haben alle Antezedens-Kanten denselben wirksamen Typ, gilt dieser, sonst `fw:FuzzinessWobbliness`; eine Kante ohne Typ zählt als `fw:Vagueness`. Die Regel steht nicht in der FW-Ontologie (D16) | 2026-10-30 |
| Hextupel: Methoden-IRIs | Die sechs Logiken (`amt:GoedelLogic`, `amt:ProductLogic`, `amt:LukasiewiczLogic`, `amt:EinsteinProduct`, `amt:GeometricMean`, `amt:HamacherProduct`) werden in `ontology/amt.ttl` zusätzlich `fw:PropagationMethod`; `amt.ttl` bekommt den Präfix `fw:`. Der Vorschlag in `data/amt-alignment.ttl` der FW-Ontologie wird damit überflüssig (D16) | 2026-10-30 |
| Hextupel: Datentyp der Gewichte | Die Turtle-Ausgabe schreibt `amt:weight` als `xsd:decimal` statt `xsd:double`; `amt:WeightShape` bleibt unverändert. Die Ausgabe jedes Beispiels ändert sich dadurch einmalig, das steht im CHANGELOG (Befund 2026-10-30, D15) | 2026-10-30 |
| Hextupel: Evidenz | `fw:derivedFrom` und der Evidenzknoten (z. B. `fw:TextEvidence` mit `fw:sourceString`) werden gelesen und unverändert in die Ausgabe geschrieben; die Engine rechnet nichts damit, abgeleitete Kanten bekommen kein `fw:derivedFrom` (D13) | 2026-10-30 |
| Hextupel: Schnitt und Version | Drei Patches: (1) S19 und S20 in beiden Repos, (2) S21 und S22 in der Engine (zusammen, weil `tests/test_js_reasoner.py` Python und JS gemeinsam prüft), (3) S23 mit Runner, Release und Zenodo. Die Änderung ist additiv, daher Engine 0.6.0 und Runner 0.5.0 | 2026-10-30 |
| Folge für das Mini-AMT-Repo | `leiza-scit/CHNT2026-amt` ordnet sichere Aussagen laut Chat vom 2026-10-30 bisher „ohne Typ“ zu; mit dem Standard „vage“ muss das nachgezogen werden (D17) | 2026-10-30 |
| Hextupel: Inverse, Subsumption, Mehrfachableitung | `InverseAxiom` und `SubsumptionAxiom` setzen keine Methode und übernehmen den Typ der Quellkante. Bei Mehrfachableitung liefert der Weg mit dem höchsten Gewicht Typ und Methode, bei Gleichstand die kleinste Methoden-IRI (sortiert, deterministisch) | 2026-10-30 |
| Hextupel: Gleichstand genauer | Bei Mehrfachableitung mit gleichem Gewicht gilt der kleinere Schlüssel `(Methoden-IRI, Typ-IRI)`; eine Kante ohne Methode sortiert zuerst. Ein anderer Typ zählt als Änderung für den Fixpunkt, eine andere Methode nicht (sonst steigt die Zahl der Durchläufe, ohne dass sich etwas ändert). Bekannte Grenze: ändert sich der Typ einer Antezedens-Kante erst nach der Ableitung bei gleichem Gewicht, bleibt der früher abgeleitete Typ, wenn er der kleinere Schlüssel ist (deterministisch, aber nicht neu berechnet) | 2026-10-30 |
| Hextupel: Methode an abgeleiteten Kanten | Jede von einer Rollenkette abgeleitete Kante trägt `fw:hasMethod` (die Logik), auch wenn ihr Typ der Standard ist; deshalb enthält `*.reasoned.ttl` auch bei Dateien ohne Typ den Präfix `fw:` und `fw:hasMethod` (im CHANGELOG genannt). Nur `fw:hasType` des Standards wird nicht geschrieben | 2026-10-30 |
| Hextupel: Ausgabeformate | `edges.csv` bekommt am Ende die Spalten `type` (wirksamer Typ, also `fw:Vagueness` statt leer) und `method` (leer, wenn keine); Cypher-Eigenschaften `type` und `method` (Kurznamen, `method` nur wenn vorhanden); Tooltip im Graphen und im Explorer: `asserted\|inferred \| type: … \| method: …` | 2026-10-30 |
| Hextupel: Evidenz | Evidenz-Knoten werden mit ihren eigenen Tripeln gelesen (Objekte, die Blank Nodes sind, entfallen: keine verschachtelten Knoten) und als `fw:derivedFrom [ … ]` wieder geschrieben; der Explorer führt Evidenz nicht mit | 2026-10-30 |
| Eingabe als Text | `load_amt` und `validate_against_shapes` behandeln einen Text, der kein Pfad sein kann („File name too long“), als Turtle; Fehler beim Prüfen des Pfads gelten als „kein Pfad“ (`is_existing_path` in `amt/core.py`) | 2026-10-30 |
| Namensräume der Beispiele | Die Bezeichner der Beispieldaten ziehen mit um: `http://github.com/alpaca-fair-framework/amt-explore/` (animals, SKOS-Beispiele) und `http://github.com/alpaca-fair-framework/amt-engine/subsumption-demo/`; die Pfade bleiben, nur der Organisationsname ändert sich. Der Vorschlag war, sie als stabile Bezeichner zu belassen; der Autor hat anders entschieden. Dateien mit dem alten Namensraum laden und validieren weiter | 2026-10-30 |
| Adressen nach dem Umzug | Pages: `https://alpaca-fair-framework.github.io/amt-engine/` (am 2026-10-30 geprüft: lädt; `n4o-rse.github.io/amt-engine/` antwortet nicht). `deploy/redirects.yaml` hat die neue `pages`-Adresse und die neuen Repo-Ziele; die `.htaccess`-Dateien und die w3id-README entstehen daraus. Historische Texte (Prosa im CHANGELOG des Runners, ältere Einträge in diesem Primer) bleiben unverändert | 2026-10-30 |
| Ausspielen der Weiterleitungen | Die erzeugte `deploy/academic-meta-tool.xyz/.htaccess` lädt der Autor per FTP neu hoch; für `w3id.org/amt/` stellt er einen neuen Pull Request in `perma-id/w3id.org` mit `deploy/w3id/ids/amt/.htaccess` und README; danach `python py/check_redirects.py` | 2026-10-30 |

Jede Zeile bekommt ein Datum. Vorschläge heißen `Vorschlag` und werden in dem Schritt bestätigt, in dem sie zuerst wirken. Überholte Beschlüsse werden mit neuem Datum und Grund umgeschrieben, nicht gelöscht.

### A5 Was in welchem Chat hochgeladen wird

`PRIMER.md` plus ein Bundle der Quellen, ohne erzeugte Dateien und ohne die großen Bilder:

```cmd
robocopy . %TEMP%\amt-engine-bundle /E /XD .git .venv build dist __pycache__ .pytest_cache amt.egg-info /XF *.png *.zip
```

```cmd
powershell -NoProfile -Command "Compress-Archive -Path $env:TEMP\amt-engine-bundle\* -DestinationPath amt-engine-bundle.zip -Force"
```

`robocopy` meldet bei Erfolg Exit-Code 1; das ist kein Fehler. Nicht hochladen: `.venv/`, `.git/`, `build/`, `dist/`, `*.egg-info/`, Ausgaben unter `out/`.

### A6 IRI-Landkarte

Entfällt in diesem Repo. Der Namensraum `http://academic-meta-tool.xyz/vocab#` wird nicht aus diesem Repo ausgeliefert; `ontology/amt.ttl` ist die Quelle. Wo er aufgelöst wird, steht in D2.

---

## Teil B – Schrittübersicht

| ID | Schritt | Repo | hängt ab von | Status |
|---|---|---|---|---|
| S0 | Festlegungen: Reihenfolge, Orchestrator, Uhr, CHANGELOG | amt-engine | – | erledigt 2026-10-26 |
| S1 | Skeleton: `PRIMER.md`, `main.py`, `py/`, `CHANGELOG.md`, `CITATION.cff`, README | amt-engine | S0 | erledigt 2026-10-26 |
| S1a | Nachbesserung nach dem Windows-Lauf: `docs-sync` und Zeilenenden, Primer-Befunde | amt-engine | S1 | erledigt 2026-10-26 |
| S2 | `amt-runner` auf das Muster: `PRIMER.md`, `CHANGELOG.md`, `CITATION.cff`, `requirements.txt`, Dev-Pipeline (im Runner-Primer als S1 geführt) | amt-runner | S1 | erledigt 2026-10-26 |
| S3 | `CITATION.cff` klären: Autorenliste, ORCID, Rolle von Unold und Mees | amt-engine, amt-runner | S1 | erledigt 2026-10-26 |
| S4 | CI: GitHub Action mit `python main.py --strict` bei Push und Pull Request | amt-engine | S1 | erledigt 2026-10-26 |
| S5 | Tags `v0.1.0` bis `v0.3.0` setzen, Release 0.3.1, Zenodo-DOI | amt-engine | S3, S4, S6 | erledigt 2026-10-26 |
| S6 | `requirements-dev.txt` in `requirements.txt` einfassen; Folge für den Runner prüfen (er installiert aus dieser Datei) | amt-engine | S1, S2 | erledigt 2026-10-26 |
| S7 | Offene Punkte aufräumen: D3 (Warnungen), D7 (Reihenfolge), D4 und D5 (Beschlüsse), D2 (Befund) | amt-engine, amt-runner | S5 | erledigt 2026-10-26 |
| S8 | Node-24-Korrektur: `upload-artifact@v5` auf `@v6` | amt-engine, amt-runner | S7 | erledigt 2026-10-26 |
| S9 | Vokabular und Ontologie ins Repo: Seiten, `amt.rdf`, Abbildungen aus Code (Schritt `site`) | amt-engine | S7 | erledigt 2026-10-26 |
| S10 | Startseite (Englisch und Deutsch, Hell/Dunkel, Was AMT kann und nicht kann, Geschichte), Explorer nach `/explorer/` | amt-engine, amt-runner | S9 | erledigt 2026-10-26 |
| S11a | Gemeinsamer JS-Reasoner (Port der Python-Engine, Paritätstest), Explorer mit Beispielliste und „TTL laden“, schlankes Layout | amt-engine | S10 | erledigt 2026-10-26 |
| S11b | Playground (`leiza-rse/amt-playground`): nur Personen-Interessen-Netzwerk, ohne Triplestore und ohne Datei laden, mit dem gemeinsamen Reasoner | amt-playground | S11a | Patch geliefert (`patch-s11b-playground.zip`), nach Push erledigt |
| S11c | Gestaltung: Farbwelt aus den Maskottchen (`design/palette.yaml`), Logos, Kopfleiste, Familien-Abschnitt, Explorer startet mit `animals` | amt-engine | S11a | Patch geliefert, nach Push erledigt |
| S11d | Logos der Institutionen und Förderer (mainzed, i3mainz, LEIZA, NFDI4Objects, NFDI, DFG) im Fuß aller Seiten; Explorer-Kasten mit Pinguin | amt-engine | S11c | Patch geliefert, nach Push erledigt |
| S12 | w3id-Eintrag (`w3id.org/amt/`) und Umleitung des FTP (`.htaccess`) auf GitHub Pages | amt-engine | S9, S10 | erledigt 2026-10-27 (FTP live; w3id-PR gestellt) |
| S14 | Texte (Namensgeschichte B, Familiensatz), Bibliografie, Bibliotheken lokal, w3id-Header aus der YAML und Adresse ohne `ids/`, `preferred-citation`, Seitentest | amt-engine | S12 | Patch geliefert, nach Push erledigt |
| S13 | D6 (Exit-Code, unverändert) und Release 0.4.0 (Engine) / 0.3.0 (Runner) samt Zenodo | amt-engine, amt-runner | S10 bis S12, S14 | 13a und 13b erledigt (Tag `v0.4.0`, Release, Zenodo); 13c als Patch geliefert |
| S15 | Schrift: Roboto lokal (Seiten und PNG-Figuren), Beschluss D10 | amt-engine | S13 | Patch geliefert |
| S16 | Nutzerfreundliche Validierung: Diagnose (`AMT-E…`), SHACL-Meldungen mit Knoten, `--check-only`/`--strict`, viz ohne Absturz, How-To-Sektion | amt-engine, amt-runner | S15 | erledigt 2026-10-27 |
| S17 | How-To-Seite „Run and look at the result“: klonen, Datei ablegen, prüfen, laufen lassen, Ergebnis lesen (Windows-`cmd`, Hinweise für Linux/macOS) | amt-engine | S16 | erledigt 2026-10-27 (Windows, Python 3.10) |
| S18 | Release 0.5.0 (Engine) / 0.4.0 (Runner) samt Zenodo | amt-engine, amt-runner | S16, S17 | 18a und 18b erledigt (Tag `v0.5.0`, Release, Zenodo); 18c als Patch geliefert |
| S19 | Adressen auf `alpaca-fair-framework` umstellen (Quellen, erzeugte Seiten, Tests, `CITATION.cff`, Weiterleitungen) | amt-engine, amt-runner | S18 | erledigt 2026-10-30 (Push, `.htaccess`, Zenodo durch den Autor gemeldet) |
| S20 | Hextupel: Festlegungen, kein Code (Datentyp der Gewichte, Konfliktfall, Diagnose-Codes, Methode bei Inverse und Subsumption, Mehrfachableitung, Evidenz) | amt-engine | – | Patch geliefert, nach Push erledigt |
| S21 | Hextupel in der Python-Engine: laden, Reasoning, Export, SHACL, Diagnose, How-To, Tests, Roundtrip-Beispiel | amt-engine | S19, S20 | Patch geliefert (zusammen mit S22) |
| S22 | Hextupel im JS-Port und im Explorer, Paritätstest | amt-engine | S21 | Patch geliefert (zusammen mit S21) |
| S23 | Runner (Beispiel, Dokumentation, Versions-Hinweis), Release Engine 0.6.0 und Runner 0.5.0 samt Zenodo | amt-engine, amt-runner | S21, S22 | offen |

S3, S4, S5 und S6 sind erledigt. Offen bleiben die Punkte in Teil D. Der Runner (S2) liest die Engine zur Laufzeit aus `main`; er braucht S5 erst, wenn er auf Tags pinnen soll.

S19 und S20 sind voneinander unabhängig: S20 ist nur Text und Entscheidung und kann vor, nach oder neben S19 laufen. S19 sollte vor S21 liegen, damit die Patches lesbar bleiben (Adressen und Logik nicht in einem Diff). Der Runner folgt jeweils im eigenen Chat (S10 und S11 im Primer von `amt-runner`).

Status ist `offen`, `erledigt <Datum>` oder `hinfällig`. Schritt-IDs werden nie umnummeriert.

---

## Teil C – Die Schritte

## S1 – Skeleton für amt-engine

**Ziel:** Das Repo trägt Plan, Entwicklungs-Pipeline, Änderungsprotokoll und Zitierangabe, ohne dass sich das Verhalten von `amt` oder `amt-runner` ändert.

**Uploads:** `PRIMER.md` und das Bundle aus A5.

**Inhalt:**

- `main.py` mit `--list`, `--only`, `--from`, `--skip`, `--dry-run`, `--strict`; Schritte starten als Kindprozesse, `PYTHONIOENCODING=utf-8`, Zeittabelle am Ende.
- `py/amt_dev_utils.py` mit `RELEASE`, `RELEASE_DATE`, Pfaden, `Report` und `run_python()`.
- Sechs Schritte: `meta`, `ontology`, `tests`, `examples`, `determinism`, `docs-sync`; jeder auch einzeln startbar (`python py/step_tests.py`).
- `CHANGELOG.md`, `CITATION.cff`, README-Abschnitt „Development" und die Korrektur des Layouts.

**Abnahme:** `python main.py --strict` auf einem Checkout, in dem `docs/data/` schon synchron ist, endet mit Exit-Code 0; zweimal hintereinander, `git status` beim zweiten Mal sauber; `python main.py --list` nennt sechs Schritte; `pytest` meldet weiterhin 62 grüne Tests.

### Erledigt 2026-10-26

- Gesamtlauf rund 15 Sekunden: `tests` 8,1 s (52 %), `examples` 4,2 s, `determinism` 2,6 s, `ontology` 0,5 s.
- `docs-sync` hat beim ersten Lauf `docs/data/subsumption-demo.ttl` angelegt (siehe Befund in A1); diese Datei gehört in den Commit, wird aber vom Lauf erzeugt, nicht mit dem Patch geliefert.
- Der Determinismus-Test läuft ohne Abweichung; er vergleicht fünf Dateien je Beispiel und schließt `*.report.md` aus (A4).
- Gegenprobe: `docs/data/subsumption-demo.ttl` gelöscht, dann `python main.py --strict --only docs-sync` endet mit Exit-Code 1; `__version__` auf 0.3.1 gesetzt, dann bricht `meta` mit Exit-Code 1 ab. Beide Prüfungen schlagen also an, wenn sie sollen.
- Verifiziert gegen einen frischen Klon von `a50822c` in einer neuen virtuellen Umgebung (Linux, Python 3.13). Am selben Tag hast du den Patch auf Windows angewendet und committet (`9a0e8b7`); der Lauf dort ist in A1 festgehalten.

## S1a – Nachbesserung nach dem Windows-Lauf

**Ziel:** `python main.py --strict` besteht auf Windows und Linux gleichermaßen, und der Primer hält fest, was der Windows-Lauf gezeigt hat.

**Uploads:** `PRIMER.md`, `py/step_docs_sync.py`, Terminal-Ausgabe des Windows-Laufs.

**Abnahme:** In einem Checkout, dessen `docs/data/` inhaltlich synchron ist, meldet `python main.py --only docs-sync` kein `WARN`, auch wenn die Dateien in einem Verzeichnis CRLF und im anderen LF haben; `python main.py --strict` endet mit Exit-Code 0; eine echte inhaltliche Abweichung führt weiterhin zu `WARN` und mit `--strict` zu Exit-Code 1.

### Erledigt 2026-10-26

- Gegenprobe unter Linux: `docs/data/*.ttl` in CRLF umgewandelt, danach kein `WARN` und keine Änderung der Dateien; Inhalt einer Datei verändert, danach `WARN updated`, mit `--strict` Exit-Code 1.
- Windows bestätigt am 2026-10-26 (Commit `41620dd`): `python main.py --strict` endet grün in 31,8 s, `docs-sync` meldet `6 file(s) already in sync` ohne `WARN`.

## S2 – amt-runner auf das Muster

**Ziel:** `amt-runner` trägt Plan, Dev-Pipeline, Tests, Änderungsprotokoll und Zitierangabe, ohne dass sich das Verhalten von `run_amt.py` ändert.

**Uploads:** `PRIMER.md` aus diesem Repo; der Runner wurde über den GitHub-Klon gelesen.

**Abnahme:** siehe `PRIMER.md` im Repo `amt-runner`, Schritt S1.

### Erledigt 2026-10-26

- Details, Befunde und Beschlüsse stehen im Primer von `amt-runner`. Für dieses Repo folgen daraus zwei Beschlüsse (A4): eine `requirements.txt` pro Repo und `main` als Standard-Ref des Runners.
- Der Runner installiert die Pakete aus `requirements.txt` dieses Repos. Fasst S6 `requirements-dev.txt` dort ein, installiert der Runner künftig auch `pytest`. Entschieden in S6: darf mitkommen.

## S3 – Autoren, ORCID und Rechteinhaber klären

**Ziel:** `CITATION.cff`, `pyproject.toml` und `LICENSE` nennen in beiden Repos dieselben Personen und denselben Rechteinhaber; S5 kann daraus eine Zenodo-Veröffentlichung ableiten.

**Uploads:** `PRIMER.md`; die Antworten kamen aus einem Formular (Autoren, ORCID, Rechteinhaber, Metadaten).

**Inhalt:** Autorenliste Thiery und Mees mit ORCID und Affiliation LEIZA in beiden `CITATION.cff`; `references` mit dem ursprünglichen Academic Meta Tool in der Engine; `pyproject.toml` der Engine mit denselben Autoren; Rechteinhaber in beiden `LICENSE`; CHANGELOG-Einträge.

**Abnahme:** `python main.py --strict` grün, zweimal hintereinander, `git status` beim zweiten Mal sauber; `pip install -e .` funktioniert weiter und `pip show amt` nennt die beiden Autoren; `docs/LICENSE` und `docs/js/LICENSE` sind unverändert.

### Erledigt 2026-10-26

- Entscheidungen stehen in A4. D1 ist damit geklärt.
- Der Runner-Primer wurde im selben Patch nachgezogen (Rechteinhaber, Autoren, Windows-Befund).
- Die Zenodo-DOI kam in S5 (5c); der Kommentar in `CITATION.cff` ist ersetzt.

## S4 – CI mit GitHub Actions

**Ziel:** Jeder Push auf `main` und jeder Pull Request läuft durch `python main.py --strict`, auf Linux und Windows.

**Uploads:** `PRIMER.md`, `README.md`, `CHANGELOG.md`; die Antworten kamen aus einem Formular (Betriebssysteme, Python-Versionen, Auslöser).

**Inhalt:** `.github/workflows/ci.yml` mit vier Jobs (Ubuntu und Windows, Python 3.10 und 3.13), `fail-fast: false`, nur Leserechte, laufende Läufe desselben Branches werden abgebrochen; Abhängigkeiten aus `requirements-dev.txt` (S6 stellt das auf `requirements.txt` um); Report je Job als Artefakt.

**Abnahme:** Nach dem Push zeigt der Reiter „Actions“ den Lauf `CI` mit vier grünen Jobs. Der Commit des Sync-Workflows (`[skip ci]`) startet ihn nicht.

### Erledigt 2026-10-26

- Der Workflow ist mit `actionlint` geprüft; ein echter Lauf war hier nicht möglich (kein Zugriff auf Actions). Die erste Rückmeldung kommt aus dem Reiter „Actions“ nach deinem Push.
- Auf den Windows-Runnern checkt Git mit `core.autocrlf=true` aus; das ist derselbe Fall wie bei dir und seit S1a durch den normalisierten Vergleich in `docs-sync` abgedeckt.
- `sync-examples-to-docs.yml` bleibt unverändert. Seine Commits tragen `[skip ci]`; der Workflow läuft nur bei Änderungen in `examples/**` und prüft nicht selbst.

## S5 – Tags, Release 0.3.1 und Zenodo-DOI

**Ziel:** Die Software ist zitierbar: Tags für die drei bisherigen Versionen, ein erstes GitHub-Release `v0.3.1` und eine Zenodo-DOI in `CITATION.cff` und README.

**Uploads:** Zwei Patches (5a, 5c) und manuelle Befehle für die Tags (5b); die Antworten kamen aus einem Formular.

**Teil 5a (Patch):** Version 0.3.1 in `pyproject.toml`, `amt/__init__.py`, `CITATION.cff`, `py/amt_dev_utils.py` und `CHANGELOG.md` (`[Unreleased]` wird `[0.3.1] - 2026-10-26`, Vergleichslinks auf Tags).

**Teil 5b (manuell, nach dem Push von 5a):** annotierte Tags `v0.1.0` auf `3357cde`, `v0.2.0` auf `5cc2fbf`, `v0.3.0` auf `03eb093` und `v0.3.1` auf dem Commit von 5a; `git push origin --tags`; auf GitHub ein Release aus `v0.3.1` anlegen. Nur dieses Release löst bei Zenodo die Archivierung aus.

**Teil 5c (Patch):** Zenodo-DOI (Concept-DOI) in `CITATION.cff` und README eintragen, `[Unreleased]` im CHANGELOG ergänzen. Das ist ein Patch nach dem Release, weil die DOI vorher nicht bekannt ist.

**Abnahme:** `python main.py --strict` grün; `git tag` zeigt vier Tags; die Seite „Releases“ zeigt `v0.3.1`; auf zenodo.org steht eine Version mit den Autoren aus `CITATION.cff`; nach 5c nennt `CITATION.cff` die DOI.

### Erledigt 2026-10-26

- 5a: Commit `359b29f` (Version 0.3.1); Windows-Lauf von `python main.py --strict` grün (34,9 s).
- 5b: Tags `v0.1.0` bis `v0.3.1` gesetzt und gepusht, GitHub-Release `v0.3.1` angelegt.
- Zenodo hat das Release archiviert: Version `10.5281/zenodo.23669467`, Concept-DOI `10.5281/zenodo.23669466` (Seite „Cite all versions“). Titel, Beschreibung und beide Autoren mit ORCID stammen aus `CITATION.cff`.
- 5c: DOI in `CITATION.cff`, Abschnitt „Citation“ im README, CHANGELOG unter `[Unreleased]`. Zenodo archiviert nur Releases; dieser Commit löst nichts aus.
- Der nächste Release (0.3.2 oder 0.4.0) bekommt eine eigene Versions-DOI; die Concept-DOI bleibt gleich.

## S6 – requirements-dev.txt einfassen

**Ziel:** Dieses Repo hat genau eine `requirements.txt`, wie A3 es verlangt.

**Uploads:** Bundle aus A5; die Antworten kamen aus einem Gespräch (`pytest` beim Runner: darf mitkommen; Actions-Versionen im selben Patch).

**Inhalt:** `pytest>=7.0` steht mit Kommentar in `requirements.txt`; `requirements-dev.txt` entfällt (Löschung als manueller Schritt: `git rm requirements-dev.txt`, ein ZIP kann sie nicht transportieren); README (Layout und Hinweis zum Vendoring) und `ci.yml` verweisen auf die eine Datei; `[project.optional-dependencies] dev` in `pyproject.toml` bleibt, damit `pip install -e ".[dev]"` weiter geht. In beiden `ci.yml` steigen die Actions auf `checkout@v5`, `setup-python@v6` und `upload-artifact@v5` (Node 24).

**Abnahme:** `pip install -r requirements.txt` in einer neuen virtuellen Umgebung, danach `python main.py --strict` grün; `python run_amt.py animals.ttl` im Runner läuft weiter durch (und installiert jetzt `pytest` mit); nach dem Push zeigt „Actions“ vier grüne Jobs je Repo ohne die Node-20-Warnung; `git status` sauber.

### Erledigt 2026-10-26

- Siehe Abnahme; was auf Actions passiert, zeigt erst der Lauf nach dem Push.
- Der Runner liest zur Laufzeit die `requirements.txt` aus dem geklonten Engine-Stand (`main`), nicht aus diesem Commit: Solange der Patch nicht gepusht ist, installiert er weiter ohne `pytest`.

## S7 – Offene Punkte aufräumen

**Ziel:** Teil D enthält nur noch, was wirklich offen ist.

**Uploads:** `PRIMER.md`; Antworten aus einem Formular (D5, Netz-CI des Runners, D7, D4).

**Inhalt:** D3: Ursache klären und die zwei Deprecation-Meldungen filtern. D7: Verstöße sortieren, mit Test. D4 und D5: Beschlüsse in A4. D2: Befund notieren.

**Abnahme:** `python main.py --strict` grün, zweimal hintereinander; `pytest` meldet 63 Tests ohne Warnungen (unter Linux; unter Windows meldet der Lauf noch 204, siehe D8); fünf Läufe von `python ontology/validate_examples.py` unter verschiedenen `PYTHONHASHSEED` geben die Verstöße in derselben Reihenfolge aus; `git status` sauber.

### Erledigt 2026-10-26

- D3: Die Warnungen stammen nicht aus diesem Paket. `pyshacl` (0.40.1) ruft beim Erzeugen des Berichts `hash()` auf einem rdflib-`Dataset` auf (`validator.py`, `create_validation_report`), und rdflib 7.6 meldet dafür `Dataset.identifier` und `Dataset.default_context` als veraltet, einmal pro Aufruf. Behebbar ist das nur in pyshacl oder rdflib; hier ist es gefiltert, und die Filter sind in `pyproject.toml` begründet. Bei einem späteren pyshacl-Update prüfen, ob sie noch gebraucht werden.
- D7: Die Gegenprobe zeigte, dass die Reihenfolge unter Linux stabil ist und nur auf Windows wechselt; deshalb prüft der Test die Sortierung an einem absichtlich falsch geordneten Bericht. Ohne die Sortierzeile schlägt er an.
- D2: Der Abruf von `http://academic-meta-tool.xyz/vocab` liefert eine HTML-Seite mit der Vokabular-Dokumentation, nicht Turtle; das RDF liegt laut Seite getrennt unter dem Namen `amt.rdf`, der Abruf von dort schlug fehl. Die Seite nennt drei Logiken (Łukasiewicz, Product, Gödel) und keine Subsumption; `ontology/amt.ttl` hat sechs Logiken und `SubsumptionAxiom`. Das spricht dafür, dass die veröffentlichte Fassung älter ist. Das ist ein Befund aus einer Zusammenfassung der Seite, kein Vergleich der Dateien; D2 bleibt offen.
- D4 und D5: Beschlüsse in A4.
- D6 bleibt unverändert (Beschluss vom 2026-10-26).

## S8 – Node-24-Korrektur

**Ziel:** Die Node-20-Warnung in den Actions verschwindet.

**Inhalt:** `actions/upload-artifact` von v5 auf v6 in allen Workflows beider Repos; die falsche Aussage aus S6 (v5 laufe auf Node 24) in A4, `CHANGELOG.md` und `PRIMER.md` berichtigt.

**Abnahme:** Nach dem Push zeigt der Actions-Lauf keine Node-20-Meldung mehr.

### Erledigt 2026-10-26

- Geprüft an `action.yml` der Tags: `upload-artifact@v5` hat `using: node20`, `@v6` und `@v7` `node24`; `checkout@v5` und `setup-python@v6` waren schon `node24`. Beide CI-Läufe nach dem Push grün.

## S9 – Vokabular und Ontologie ins Repo

**Ziel:** Die Dokumentation der Namensraum-IRI liegt im Repo, wird aus `ontology/amt.ttl` erzeugt und kann nicht mehr hinter der Ontologie zurückbleiben.

**Uploads:** die beiden Ordner `vocab` und `ontology` sowie der Rest des FTP (`amt.rdf`, Demos, Playground) aus `academic-meta-tool.xyz`.

**Inhalt:** Neuer Schritt `site` (`py/step_site.py`, `py/site_pages.py`, `py/site_figures.py`, `py/amt_site.py`): erzeugt `docs/vocab/` (Seite, `amt.ttl`, `amt.rdf`, `amt.jsonld`, Übersichtsabbildung) und `docs/ontology/` (Datenmodell mit Beispielen und neun Abbildungen). Metadaten (Autoren, Datum, Lizenz, Quelle) stehen jetzt im `owl:Ontology`-Knoten von `ontology/amt.ttl`. Gemeinsames Stylesheet und Hell/Dunkel-Umschalter in `docs/assets/`. Tests in `tests/test_site.py`: jeder Begriff hat eine Karte, die Übersicht folgt der Ontologie, jedes Turtle-Beispiel besteht die SHACL-Prüfung, SVG ist deterministisch.

**Abnahme:** `python main.py --strict` grün, zweimal hintereinander (der erste Lauf erzeugt die Dateien unter `docs/` und meldet sie als Warnung; danach committen); `git status` sauber; Seiten lokal in Hell und Dunkel ansehen, auch schmal.

### Erledigt 2026-10-26

- D2 geklärt: `amt.rdf` von 2018 (Penny Edition) hat 25 Begriffe, alle sind in `ontology/amt.ttl` mit gleicher IRI enthalten; neu sind 20 (u. a. `SubsumptionAxiom`, `antecedents`, `HamacherProduct`, `ReasoningRule`). Die Logiken waren 2018 Klassen, heute sind sie Instanzen von `amt:Logic`; 2018 stand zusätzlich `owl:Class`, `owl:ObjectProperty` und `owl:DatatypeProperty` an den Begriffen.
- Der Test der Beispiele fand, dass jede Rolle ein `rdfs:label` braucht (SHACL); die Beispiele sind entsprechend ergänzt.
- `amt.rdf` wird als Graph verglichen, nicht byteweise: die Byte-Reihenfolge des Serialisierers kann sich zwischen rdflib-Versionen ändern, der Inhalt nicht.
- Nicht Teil von S9: Startseite (S10), Playground (S11), Umleitung und w3id (S12). Der Link „Explorer“ zeigt bis S10 auf `index.htm`.

## S11a – Gemeinsamer JS-Reasoner und Explorer

**Ziel:** Der Explorer rechnet wie die Python-Engine, zeigt alle Beispiele und lädt eine eigene TTL-Datei.

**Inhalt:** `docs/js/amt-reasoner.js` (Port von `amt/reasoning.py` und `amt/logic.py`, ohne `minimal`-Modus, UMD für Browser und Node); `docs/js/amt.js` nutzt ihn, liest `amt:antecedents`-Listen, `SubsumptionAxiom`, `logicParameter` und kennt auch Dateien ohne Axiom-Hierarchie; Quelle wählbar (`window.AMT_SOURCE`: URL oder `{text, name}`); `docs/explorer/index.html` neu und schlank (eine Leiste), Beispielwahl aus `docs/data/examples.json` (erzeugt von `docs-sync`), TTL laden, Statuszeile mit Konsistenz; Exporte mit Listen und Provenienz; `tests/test_js_reasoner.py` (Parität mit Python, braucht Node, sonst übersprungen). Schritt `docs-sync` läuft jetzt vor `site` und `tests`.

**Befund:** Der alte Explorer zeigte bei Reasoning an für das Potter-Beispiel nichts Neues (7 Kanten), weil es `amt:antecedents` nutzt, das der alte Code nicht las.

**Abnahme:** `python main.py`, dann `--strict` zweimal grün; im Browser Beispiel wählen, Reasoning an (Potter: 8 rote Kanten, animals: 106, skos-mapping: Hinweis auf 2 Verletzungen), eigene Datei laden.

**Nicht Teil:** der leiza-Playground (S11b, eigener Patch; `docs/js/amt-reasoner.js` ist die Quelle, der Playground hält eine Kopie).

### Nachtrag 2026-10-26

- CI rot nach dem Push von S11a: `docs-sync` sortierte `Path`-Objekte; unter Windows vergleichen Pfade ohne Groß/Kleinschreibung, unter Linux mit. Die Reihenfolge in `examples.json` war dadurch plattformabhängig (lokal grün, auf Windows und im CI rot). Jetzt nach `(name.lower(), name)`. Lehre: Pfade nie als Objekte sortieren, wenn die Reihenfolge in eine erzeugte Datei oder einen Test eingeht.
- Der Explorer-Schalter ist beschriftet (aus grau, an rot) und ein Kasten unten rechts nennt Herkunft und Förderung (mainzed, i3mainz, RGZM/LEIZA, NFDI4Objects, DFG 501836407); derselbe Satz steht im Fuß aller erzeugten Seiten.

## S10 – Startseite und Explorer unter /explorer/

**Ziel:** Eine Startseite am Root von `docs/`, die erklärt, was AMT ist, kann und nicht kann, woher es kommt und wie man es zitiert; der Explorer zieht nach `/explorer/` um.

**Inhalt:** `py/site_home.py` erzeugt `docs/index.html` (Englisch bevorzugt, Deutsch umschaltbar, Hell/Dunkel; beide Sprachen im selben Dokument, `data-lang` an `<html>`, Wahl in `localStorage`). `docs/explorer/index.html` ist der bisherige Explorer; `docs/index.htm` ist nur noch eine Weiterleitung, die `?ttl=…` und `#…` mitnimmt; `docs/js/amt.js` sucht relative `?ttl=`-Pfade eine Ebene höher (`../data/…`). Schritt `site` läuft jetzt vor `tests`, damit der Link-Test die frisch erzeugten Seiten sieht. D8 geschlossen: `pyproject.toml` filtert `Dataset.contexts is deprecated`. Runner: Link im README auf `/explorer/`.

**Abnahme:** `python main.py` (erster Lauf erzeugt Dateien), danach `python main.py --strict` zweimal grün; Startseite in Hell und Dunkel, Englisch und Deutsch ansehen; `https://n4o-rse.github.io/amt-engine/index.htm?ttl=data/animals.ttl` landet im Explorer.

### Erledigt 2026-10-26

- Der Explorer-Code deckt nur den Stand von 2018 ab (drei Logiken, Ketten aus zwei Schritten, Inverse, disjunkt); Subsumtion, `antecedents` und Einstein/Geometric/Hamacher fehlen. Die Startseite sagt das offen; ob der Explorer nachgezogen wird, entscheidet sich in S11 mit dem Playground. Behoben in S11a: gemeinsamer JS-Reasoner.
- Die Namensgeschichte steht als Entwurf auf der Seite (D9): bitte im Wortlaut prüfen.
- Das Logo kommt als zweiter Schritt, sobald es vorliegt.

## S11c – Gestaltung: Farbwelt und Logos

**Ziel:** Eine eigene AMT-Farbwelt (getrennt vom LEIZA-Blau des Playgrounds), die Maskottchen auf den Seiten, der Explorer startet mit `animals`.

**Inhalt:** `design/palette.yaml` ist die einzige Quelle der Farben (Grün aus dem Fell, Bronze-Gold aus Bauch und Schnabel, Stahl-Blau aus dem Netzwerk, dazu Grund und Zustandsfarben, Tokens für Hell und Dunkel). `py/site_palette.py` erzeugt daraus `docs/assets/palette.css` (alle Seiten, auch der Explorer, binden sie vor `site.css` ein), `docs/assets/img/palette.svg|png` (die Palette als Bild) und die Hell-Werte der Abbildungen (`site_figures.TOKENS`). Schritt `site` erzeugt es mit; ein Test prüft, dass CSS, Bild und Abbildungen zur YAML passen. Logos in `docs/assets/img/`: Pinguin (groß und klein), Alpaka, Alligator, `partners.png` (mainzed, i3mainz, LEIZA, zugeschnitten aus dem alten `amt_logos.png`). Kopfleiste mit Pinguin, Startseite mit Maskottchen und Abschnitt „Teil einer Familie“ (AMT, Alpaka Research Framework, Alligator), Fuß mit Partnerlogos; Explorer in den neuen Farben, abgeleitete Kanten bleiben rot, „Reasoning: an“ ist bronze, Kanten gesetzt in Stahl. Neue Abhängigkeit PyYAML (nur Entwicklung).

**Abnahme:** `python main.py`, danach `python main.py --strict` zweimal grün; Startseite und Explorer in Hell und Dunkel ansehen.

**Offen:** Die Logos sind Pixelbilder (vektorisierte Fassungen folgen vom Autor und ersetzen sie); die Schrift ist weiter die Systemschrift (Entscheidung offen, siehe D10); der Satz im Abschnitt „Teil einer Familie“ ist ein Entwurf und braucht den Wortlaut des Autors; Links zu Alpaka und Alligator fehlen.

---

### S11d – Logos der Institutionen und Förderer

Im Fuß jeder erzeugten Seite steht eine weiße Leiste mit den Logos von mainzed, i3mainz, LEIZA, NFDI4Objects, NFDI („In cooperation with“) und DFG („Funded by“), je mit Link (`LOGOS` in `py/amt_site.py`, Bilder in `docs/assets/img/logos/`). Der Kasten im Explorer zeigt nur noch den Pinguin und den Herkunftstext mit Förderhinweis. `docs/assets/img/partners.png` entfällt. Offen: vektorisierte Fassungen der Logos; Adressen der Links bitte prüfen.

### S12 – Persistente Adressen: FTP und w3id

**Ziel:** Alle öffentlichen Adressen von AMT führen über zwei dünne Weiterleitungsschichten zu GitHub Pages; zieht das Repository um, ändert sich nur `pages` in `deploy/redirects.yaml`.

**Beschlüsse:** Der Namensraum `http://academic-meta-tool.xyz/vocab#` ändert sich nie. Das FTP von academic-meta-tool.xyz (Apache) darf geleert werden; es enthält nur noch die `.htaccess`. Der w3id-Eintrag liegt wie bei den anderen Einträgen des Autors unter `ids/` (öffentlich aber `https://w3id.org/amt/`: das `ids/` ist nur der Ordner im Repo, nicht Teil der Adresse; so fällt es 2026-10-27 auf und ist korrigiert), Kontakt Florian Thiery. w3id sichert den bestehenden Namensraum nicht gegen einen Verfall der Domain; es gibt neuen Zitaten und Links eine Adresse, die nicht an Domain und Hoster hängt. Die Vokabelseite wird per Content Negotiation bedient (Turtle, RDF/XML, JSON-LD, sonst HTML; 303 auf dem FTP, 302 bei w3id), die Anker der Termseite heißen wie die Terme.

**Inhalt:** `deploy/redirects.yaml` ist die einzige Quelle. `py/site_redirects.py` erzeugt daraus (Schritt `site`) `deploy/academic-meta-tool.xyz/.htaccess`, `deploy/w3id/ids/amt/.htaccess` und `deploy/w3id/ids/amt/README.md`, und rechnet mit `resolve()`, was jede Adresse antworten muss. `py/check_redirects.py` fragt nach dem Deployment die echten Server (mit verschiedenen `Accept`-Headern) und vergleicht; `--base-url` prüft einen Testserver. `.gitattributes` hält die Dateien in `deploy/` auf LF. Tests: Ziele existieren in `docs/`, erzeugte Dateien aktuell, Aushandlung und Altadressen.

**Abnahme:** `python main.py`, `python main.py --strict` zweimal grün. Die Regeln sind gegen einen echten Apache 2.4 geprüft (alle Fälle wie erwartet, auch `?ttl=` bleibt erhalten). Nach dem Deployment: `python py/check_redirects.py --follow`.

**Deployment (Autor):** 1. FTP leeren, `deploy/academic-meta-tool.xyz/.htaccess` als `.htaccess` ins Wurzelverzeichnis; 2. `deploy/w3id/ids/amt/` als Ordner `ids/amt/` in einen Fork von `perma-id/w3id.org` kopieren und den Pull Request stellen; 3. `python py/check_redirects.py --follow`.

### S14 – Texte, Bibliografie, Bibliotheken lokal

**Ziel:** Die Seiten laden nichts mehr von fremden Servern, der Name und die Familie haben ihren Wortlaut, und es gibt eine Bibliografie, in die Vorträge, Paper und Code-Schnipsel kommen, die AMT nennen.

**Inhalt:** (1) `docs/vendor/` enthält n3, vis, jQuery, jQuery UI, Materialize und Material Icons unverändert, mit Lizenzen und `README.md`; `docs/explorer/index.html` verweist darauf; die pyvis-HTML (`amt/viz.py`) bettet vis ein und lässt Bootstrap weg. (2) `data/bibliography.bib` mit den vier Arbeiten des Autors; `py/site_bib.py` liest sie und erzeugt `docs/bibliography/index.html` (APA 7, zweisprachige Überschriften, BibTeX je Eintrag) und `docs/bibliography/amt.bib`; Navigation und Startseite verweisen darauf. (3) Texte: Namensgeschichte B, Familiensatz ohne Links (D9). (4) `deploy/redirects.yaml` bekommt `contact`, `about` je Route und `w3id_header`; daraus entsteht der Header der w3id-`.htaccess` im Stil der Einträge archlink und cispdb; die öffentliche Adresse ist `https://w3id.org/amt/` (siehe A4). (5) `CITATION.cff`: `preferred-citation` ist der ZfdG-Artikel. (6) `tests/test_offline.py` (keine fremden Quellen, alle lokalen Links und `url(...)` lösen auf, Lizenzen der Bibliotheken), `tests/test_bibliography.py`, ein Test für den w3id-Header.

**Gegenstück im Runner:** S6 im Primer von `amt-runner` (nur Laufzeit-Abhängigkeiten, Hinweis auf den Explorer); beide Patches ändern die Versionsnummern noch nicht, das macht S13.

**Zu prüfen (Autor):** Angaben in `data/bibliography.bib` (Jahr 2023 und Titel von Thiery & Mees, Reihenfolge der Vornamen; Mees steht dort überall als „Allard W.“, in der Vorlage teils als „A.“); Vornamen von Tolle und Gampe fehlen (nur Initialen).

**Abnahme:** `python main.py` und `python main.py --strict` zweimal grün, danach `git status` sauber; im Browser lädt der Explorer ohne eine einzige Anfrage an einen fremden Server; die Seite `/bibliography/` zeigt vier Einträge.

### Nachtrag 2026-10-27 (Windows-Lauf)

Der erste Windows-Lauf (Python 3.10) zeigte einen Fehler, den die Sandbox nicht zeigen konnte: `pyvis` schreibt die HTML-Datei mit der Standard-Kodierung der Plattform (cp1252), und die eingebettete vis-Bibliothek enthält Zeichen darüber hinaus (`UnicodeEncodeError` in `test_pyvis_export_embeds_its_library_by_default`). Betroffen war jede Ausgabe mit `render_to_html`, also auch `amt --export-html` und den Runner unter Windows. Behoben in `amt/viz.py`: die Seite wird mit `generate_html()` erzeugt und von uns als UTF-8 mit LF geschrieben. Neuer Test `test_pyvis_export_does_not_depend_on_the_platform_encoding` erzwingt eine ASCII-Plattform-Kodierung (`LC_ALL=C`, `PYTHONUTF8=0`) und schlug mit dem alten Code fehl. Lehre: Dateien, die Fremdcode öffnet, kann nur ein Test mit erzwungener Kodierung prüfen; ein grüner Lauf unter Linux sagt darüber nichts.

### S13 – Release 0.4.0

**Ziel:** Die Engine 0.4.0 und der Runner 0.3.0 sind veröffentlicht, archiviert und zitierbar.

**Beschlüsse (2026-10-27):** D6 bleibt unverändert (Exit-Code 0 bei Konsistenzverletzungen). Der Runner erscheint als 0.3.0 zusammen mit der Engine 0.4.0. Der Standard-Ref des Runners bleibt `main`; die README des Runners zeigt `--ref v0.4.0` als Beispiel.

**Teil 13a (Patch):** Version 0.4.0 in `pyproject.toml`, `amt/__init__.py`, `CITATION.cff` (mit `date-released`), `py/amt_dev_utils.py` (`RELEASE`, `RELEASE_DATE`) und `CHANGELOG.md` (`[Unreleased]` wird `[0.4.0] - 2026-10-27`, Vergleichslinks); die Fußzeile der erzeugten Seiten nennt die neue Version, deshalb gehören `docs/index.html`, `docs/vocab/index.html`, `docs/ontology/index.html` und `docs/bibliography/index.html` in den Commit. Dasselbe im Runner mit 0.3.0; dort ruft der Schritt `smoke` den Runner mit `--update` auf, damit er die aktuelle Engine prüft und nicht den Cache.

**Teil 13b (manuell, nach dem Push von 13a):** je Repo ein annotierter Tag (`v0.4.0` in `amt-engine`, `v0.3.0` in `amt-runner`) auf dem Commit von 13a, `git push origin <tag>`, auf GitHub ein Release aus dem Tag. Nur das Release löst bei Zenodo die Archivierung aus.

**Teil 13c (Patch):** die Versions-DOIs in README (Abschnitt „Citation“) und CHANGELOG eintragen; die Concept-DOIs bleiben. Versions-DOIs: Engine 0.4.0 `10.5281/zenodo.23688518`, Runner 0.3.0 `10.5281/zenodo.23688616`. Zugleich ist der CHANGELOG-Eintrag 0.4.0 neu geordnet (die Release-Notes auf GitHub waren aus dem zerfaserten Eintrag entstanden: Überschriften doppelt, Einleitung widersprach dem Inhalt); der Eintrag zu 0.3.1 nennt jetzt richtig, welche Actions auf Node 24 laufen. Die Release-Notes von v0.4.0 auf GitHub werden einmal aus dem neuen Eintrag ersetzt.

**Abnahme:** `python main.py --strict` zweimal grün (Windows), `git status` sauber; `git tag` zeigt `v0.4.0` bzw. `v0.3.0`; „Releases“ zeigt es; auf zenodo.org steht je eine neue Version mit den Autoren aus `CITATION.cff`; nach 13c nennt die README die Versions-DOI.

### S15 – Schrift

**Ziel:** Alle Seiten und Figuren verwenden dieselbe Schrift, auf jedem Gerät und ohne Anfrage an einen Schriftserver.

**Beschluss (2026-10-27):** Roboto, die Hausschrift von mainzed. Die Seiten laden sie aus `docs/vendor/roboto/` (Schnitte 400, 500, 700, Latin und Latin-Ext, SIL OFL 1.1, Fontsource 5.3.0); `docs/assets/site.css` deklariert sie mit `@font-face` und `unicode-range`, `Roboto` steht vor den Systemschriften. Die PNG-Figuren zeichnet Pillow mit `design/fonts/Roboto-Regular.ttf` und `Roboto-Bold.ttf` (aus denselben woff2-Dateien umgewandelt; die Pillow-Standardschrift und das künstliche Fett per Strichstärke entfallen). `py/site_fonts.py` hält Pfade und Schriftcache; die Prüfsumme der Schriftdateien gehört zum Schlüssel in `docs/assets/figures.json`, eine geänderte Schrift zeichnet die PNGs also neu. Die Code-Schrift bleibt die Systemschrift (`ui-monospace`, Cascadia, Consolas). Der Explorer behält das ältere Roboto, das Materialize mitbringt.

**Grenzen:** SVG-Dateien, die einzeln geöffnet oder als `<img>` eingebunden werden, können keine Webschrift laden; sie fallen auf die Systemschrift zurück. Die Figuren auf den Seiten sind eingebettet und zeigen Roboto.

**Abnahme:** `python main.py` einmal (zeichnet die PNGs neu), danach `--strict` zweimal grün, `git status` sauber; im Browser lädt die Startseite nur Dateien aus `docs/`, und die Schrift ist Roboto.

### S16 – Nutzerfreundliche Validierung und How-To

**Ziel:** Wer eine AMT-Datei baut (auch per SPARQL CONSTRUCT), bekommt Fehlermeldungen, die den Knoten nennen und sagen, was zu ergänzen ist, und findet auf der Website eine Anleitung zum Bauen und Prüfen.

**Anlass:** Rückmeldung von Karsten (AFE → AMT), siehe A1, Befund vom 2026-10-27.

**Inhalt:** (1) `amt/diagnostics.py` mit `Finding`, `diagnose()`, Codes `AMT-E101`, `E102`, `E103`, `W201`, `W204`, `N301`, `N302`; (2) `amt/validation.py`: `format_violations()` und Hinweise zu den Shape-Meldungen; (3) `amt/viz.py`: Platzhalterknoten statt `AssertionError`; (4) `amt/runner.py` und `amt/cli.py`: Diagnose nach dem Laden, `--check-only`, `--strict`, `--debug`, Exit-Code 3, Abschnitt „Diagnostics“ im Report; (5) `py/site_howto.py`, Navigationseintrag „How-To“, Schaltfläche auf der Startseite (EN und DE); (6) Tests `tests/test_diagnose.py`, `tests/test_howto.py`; (7) CHANGELOG und README.

**Gegenstück im Runner:** S8 im Primer von `amt-runner` (`--check-only` im Wrapper, Erklärung der Exit-Codes, Hinweis auf `--update`).

**Für Karsten:** `python run_amt.py <datei>.ttl --update --check-only`. Ohne `--update` bleibt sein `.amt-cache` auf der alten Engine und zeigt weiter den Traceback. Die Datei braucht für die Ziele (`nm:…`) ein `amt:instanceOf` auf ein zweites Konzept (z. B. `nm:Authority`); das Rezept steht auf `howto/create/#convert` und ist getestet.

**Abnahme:** `python main.py --strict` zweimal grün, `git status` danach sauber; `amt-runner AFE_all_cases_asAMT.ttl` endet ohne Traceback und nennt `AMT-E101` mit den sieben IRIs; dieselbe Datei mit den Authority-Knoten ergänzt meldet keinen Fehler; `amt-runner x.ttl --check-only` schreibt keine Datei; die Seiten `/howto/`, `/howto/create/`, `/howto/validate/` laden ohne Anfrage an fremde Server.

### Erledigt 2026-10-27

- Sandbox: 142 Tests grün (vorher 115), `python main.py` ok (7 Schritte), Determinismus unverändert. Die Beispiele der How-To-Seiten sind getestet; das CONSTRUCT-Rezept erzeugt aus der Beispieleingabe zwei Konzepte, sieben Knoten und vier Kanten (0,5; 0,5; 0,6; 1,0), die validieren.
- Beim Bau aufgefallen: heißt das Modul wie die Funktion (`amt/diagnose.py` und `diagnose`), liefert `import amt.diagnose as d` die Funktion statt des Moduls. Deshalb `diagnostics.py`.
- Windows-Lauf am selben Tag: `python main.py` und zweimal `--strict` grün (142 Tests), CI grün (`6373b35`); mit dem Wrapper `run_amt.py --check-only --update` und einem vollen Lauf auf der reparierten AFE-Datei geprüft (11 Knoten, 7 Kanten, Graph-HTML ohne Fehler). Noch nicht geprüft: Karstens eigene Query im Original (nur `AFE_all_cases_asAMT.ttl` aus dem Anhang).

### S17 – How-To: Run and look at the result

**Ziel:** Wer nur eine `.ttl`-Datei hat, kommt von „nichts installiert“ bis zum Graphen im Browser, ohne zu raten.

**Anlass:** Rückfrage nach dem Windows-Lauf von S16: der volle Lauf stand im How-To nur als Halbsatz (wohin die Ausgabe geht, wie man den Graphen öffnet).

**Inhalt:** `howto/run/` aus `py/site_howto.py` (`howto_run()`, `RUN_OUTPUTS`): Voraussetzungen, Runner klonen, optionale venv, Datei ablegen (neben dem Runner oder per Pfad), `--check-only`, `--update`, voller Lauf, Ausgabeordner `out/run-…` und `out/latest`, Tabelle der Dateien, Graph lesen (Farben je Konzept, Dicke = Gewicht, rot gestrichelt = inferiert, grau = nicht deklariert), Explorer, erneut laufen, Fehlersuche. Verweise von `howto/`, `howto/create/` und `howto/validate/`.

**Beschluss:** Die Befehle der Seite sind für Windows-`cmd` geschrieben (A3), Linux und macOS stehen als Hinweise daneben. Die Liste der Ausgabedateien auf der Seite wird gegen einen echten Lauf getestet.

**Abnahme:** `python main.py` einmal, danach `--strict` zweimal grün, `git status` sauber; `tests/test_howto.py` prüft die Dateiliste und die Anker; die Seite `/howto/run/` lädt ohne Anfrage an fremde Server.

### S18 – Release 0.5.0 (Engine) und 0.4.0 (Runner)

**Ziel:** Diagnose, `--check-only` und die How-To-Sektion sind veröffentlicht, archiviert und zitierbar.

**Versionsentscheidung:** Neue Funktionen ohne Bruch, daher je ein Minor-Sprung: Engine 0.4.0 → 0.5.0, Runner 0.3.0 → 0.4.0. Der Reasoner und die Ergebnisdateien sind unverändert; Exit-Code 0 bei Konsistenzverletzungen bleibt (D6).

**Teil 18a (Patch):** Version in `pyproject.toml`, `amt/__init__.py`, `CITATION.cff` (mit `date-released`), `py/amt_dev_utils.py` und `CHANGELOG.md` (`[Unreleased]` wird `[0.5.0] - 2026-10-27`, Vergleichslinks); die Fußzeile der erzeugten Seiten nennt die neue Version, deshalb gehören die vier Seiten mit Fußzeile in den Commit. Im Runner `run_amt.py` (`__version__`, Pinning-Beispiel `v0.5.0`), `CITATION.cff` und `CHANGELOG.md`; der Hinweis zu `--check-only` verlangt dort Engine 0.5.0 oder neuer.

**Teil 18b (manuell, nach dem Push von 18a):** je Repo ein annotierter Tag (`v0.5.0`, `v0.4.0`) auf dem Commit von 18a, `git push origin <tag>`, auf GitHub ein Release aus dem Tag; die Release-Notes aus dem CHANGELOG-Eintrag. Nur das Release löst bei Zenodo die Archivierung aus.

**Teil 18c (Patch):** die Versions-DOIs in README (Abschnitt „Citation“) und CHANGELOG eintragen; die Concept-DOIs bleiben. Versions-DOI Engine 0.5.0: `10.5281/zenodo.23691499`; die des Runners 0.4.0 folgt mit 9c.

**Abnahme:** `python main.py --strict` zweimal grün (Windows), `git status` sauber; `git tag` zeigt die neuen Tags; „Releases“ zeigt sie; auf zenodo.org steht je eine neue Version; nach 18c nennt die README die Versions-DOI.

### S19 – Adressen auf alpaca-fair-framework umstellen

**Ziel:** Jeder Verweis auf `amt-engine`, `amt-runner` und `amt-explore` und auf die Pages-Adresse nennt die neue Organisation `alpaca-fair-framework`, ohne dass sich Verhalten oder Ergebnisdateien ändern.

**Uploads:** `PRIMER.md` und das Bundle aus A5; ein Chat je Repo, Engine zuerst, dann der Runner (S10 dort).

**Inhalt:**

- Ersetzt werden Repo-URLs und die Pages-Adresse `n4o-rse.github.io/amt-engine/` in Quellen, `CITATION.cff`, `README.md`, `deploy/redirects.yaml`, Beispiel-TTLs und Tests. Was unter `docs/` erzeugt wird, entsteht durch `python main.py` neu; `docs/data/` zieht über `docs-sync` nach.
- Treffer, bei denen die alte Adresse Teil des Belegs ist (Vorschlag: `data/bibliography.bib`, wo ein Werk seine Adresse zum Zeitpunkt der Veröffentlichung nennt), bleiben. Die Liste der belassenen Treffer steht im `PATCH-README.md`.
- Die Frage der neuen Pages-Adresse, der Weiterleitungen (FTP, w3id) und der Zenodo-Anbindung steht in D18 und wird in diesem Schritt entschieden.
- Keine Änderung an `amt/`-Verhalten, an der Ontologie oder an der Version; der Eintrag im `CHANGELOG.md` steht unter `[Unreleased]` als `Changed`.

**Abnahme:** `git grep -n "n4o-rse" -- . ":!docs/vendor"` nennt nur Treffer aus der Liste der belassenen; `python main.py --strict` zweimal grün, `git status` danach sauber; die Weiterleitungsprüfung `py/check_redirects.py` (Netz, nicht Teil von `main.py`) meldet die erwarteten Ziele.

### Erledigt 2026-10-30

- Ersetzt in 17 Quelldateien: Repo-URLs, Pages-Adresse, Issue-Adresse, Namensräume der Beispiele, Tests, `CITATION.cff`, README, `deploy/redirects.yaml` und die Verweislinks am Ende des CHANGELOG. Erzeugt durch `python main.py` neu: `docs/`, `docs/data/`, `deploy/academic-meta-tool.xyz/.htaccess`, `deploy/w3id/ids/amt/`. Danach nennt `git grep -n "n4o-rse"` in der Engine nur noch `PRIMER.md` (historische Texte).
- Die neue Pages-Adresse lädt, die alte nicht (Abruf aus der Sandbox, `client_error`). `w3id.org/amt/` und `academic-meta-tool.xyz` waren von dort nicht abrufbar; `py/check_redirects.py` wurde nicht ausgeführt, weil er die Live-Server nach dem Ausspielen prüft (A4, 2026-10-30).
- Die Namensräume der Beispiele wurden auf Wunsch des Autors mit umgestellt (A4). Der Runner muss seine Kopien gleichzeitig bekommen (S10 dort), sonst meldet `drift` Abweichungen.
- Offen, durch den Autor: FTP-Upload, Pull Request für `w3id.org/amt/`, Zenodo-Anbindung der Organisation (D18).

### S20 – Hextupel: Festlegungen

**Ziel:** Alle Entscheidungen, von denen Namen, Ausgabeformat und Verhalten des Hextupels abhängen, stehen mit Datum in A4; S21 muss nichts mehr klären.

**Uploads:** `PRIMER.md`, die aktuelle FW-Ontologie (`caa-datadragons/FW_Ontology`) und ein Beispiel mit AFE-Daten von Karsten.

**Inhalt:** Das Hextupel ist ein Quadrupel (Subjekt, Rolle, Objekt, Gewicht) plus `fw:hasType` und `fw:hasMethod`; beschlossen sind in A4 der Standard „vage“, das Lesen beider Gewichts-Properties, die Optionalität und die Regel für abgeleitete Kanten. Zu bestätigen oder umzuschreiben sind die als `Vorschlag` markierten Zeilen, als Formular mit Kommentarfeld:

- Datentyp der Gewichte in der Ausgabe (D15).
- Konfliktfall bei zwei verschiedenen Gewichten (`AMT-E104`) und die Codes `AMT-W205`, `AMT-N303`.
- Methode bei `InverseAxiom` und `SubsumptionAxiom` sowie bei Mehrfachableitung (D14).
- Evidenz (`fw:derivedFrom`) durchreichen oder mitrechnen (D13).
- Umsetzung des Standards im Kanten-Dict (`type` als IRI oder `None`, `effective_type`).
- Schnitt der Schritte und Versionssprung (0.6.0).

**Abnahme:** Jede `Vorschlag`-Zeile zum Hextupel in A4 ist bestätigt oder umgeschrieben, mit Datum; in Teil D steht keine Frage mehr, die S21 blockiert.

### Erledigt 2026-10-30

- Beschlossen im Formular am 2026-10-30: Datentyp der Gewichte `xsd:decimal` (D15), Inverse und Subsumption ohne Methode, Mehrfachableitung nach höchstem Gewicht (D14), Evidenz durchreichen (D13), Schnitt in drei Patches mit Engine 0.6.0 und Runner 0.5.0.
- Mit bestätigt, weil der Hinweis im Chat unwidersprochen blieb: Konfliktfall und die Codes `AMT-E104`, `AMT-W205`, `AMT-N303`, dazu die Umsetzung des Standards im Kanten-Dict (`type` als IRI oder `None`, `effective_type`). Wer das anders will, schreibt die Zeile in A4 um, bevor S21 beginnt.
- Offen bleiben D16 (Rückmeldung an die FW-Ontologie) und D17 (Mini-AMT-Repo); beides blockiert S21 nicht.

### S21 – Hextupel in der Python-Engine

**Ziel:** Die Engine liest, berechnet und schreibt Typ und Methode je Aussage; ein Quadrupel ohne beide verhält sich wie in 0.5.0, und die Ausgabe lässt sich wieder einlesen und validieren.

**Uploads:** `PRIMER.md`, das Bundle aus A5, die FW-Ontologie, die AFE-Beispieldatei von Karsten.

**Inhalt (nach den Beschlüssen in A4, Stand des Schritts S20):**

- `amt/core.py`: neben `amt:weight` auch `fw:hasDegreeOfConnection`; optional `fw:hasType`, `fw:hasMethod`, `fw:derivedFrom`; neue Schlüssel im Kanten-Dict (`type`, `method`, `evidence`, Standard `None`), `local_name` und die übrigen Helfer bleiben.
- neues Modul für den FW-Teil (Namensraum, die drei Typen, `effective_type`, `combine_types`); der Name folgt der Regel aus A1 (kein Modulname, der von einer Funktion in `amt/__init__.py` verdeckt wird).
- `amt/reasoning.py`: bei `RoleChainAxiom` Methode = Logik, Typ nach der Kombinationsregel; `InverseAxiom`, `SubsumptionAxiom` und Mehrfachableitung nach S20; die Reihenfolge bleibt nach IRI sortiert (Determinismus, A3).
- `amt/export.py`: Turtle (Typ, Methode, Evidenz nur wo vorhanden; Datentyp der Gewichte nach D15), Cypher-Eigenschaften, `edges.csv` mit zusätzlichen Spalten **am Ende** (damit bestehende Leser weiterlaufen), `amt/viz.py` Tooltip.
- `ontology/amt.ttl`: Präfix `fw:`, die sechs Logiken zusätzlich `fw:PropagationMethod`; `ontology/amt-shapes.ttl` bleibt für Typ und Methode ohne Pflicht; die erzeugten Vokabular-Seiten (`docs/vocab/`, `docs/ontology/`) ziehen über den Schritt `site` nach.
- `amt/diagnostics.py` und `py/site_howto.py`: die neuen Codes mit Eintrag und Anker auf der Seite „prüfen“ (`tests/test_howto.py` verlangt das für jeden Code).
- `examples/hextuple-demo.ttl` mit `.md` im Muster von `animals.md`: die drei Typen, eine Methode, eine Evidenz, erwartete Ableitungstabelle.
- Python-Code unter 3.10 prüfen (Windows-Referenz; keine Backslashes in f-String-Ausdrücken).

**Abnahme:** `python main.py --strict` zweimal grün, `git status` sauber; alle Tests aus 0.5.0 unverändert grün; ein Test liest `examples/hextuple-demo.ttl`, schreibt `*.reasoned.ttl`, liest sie wieder ein und findet dieselben Kanten mit Gewicht, Typ und Methode; die Ausgabe von `animals.ttl` besteht die Shapes (behebt den Befund vom 2026-10-30); die Kantenmenge der bestehenden Beispiele ist gegenüber 0.5.0 unverändert, in `edges.csv` kommen nur die neuen Spalten dazu.

### Erledigt 2026-10-30

- Neu: `amt/fw.py` (Namensraum, drei Typen, `effective_type`, `stored_type`, `combine_types`), `examples/hextuple-demo.ttl` und `.md`, `tests/test_hextuple.py` (23 Tests: Hilfsfunktionen, Laden, beide Gewichts-Properties, Konflikt, Ableitung, Gleichstand, Roundtrip, Shapes, CSV, Cypher, Diagnose, Ontologie). Geändert: `amt/core.py`, `reasoning.py`, `export.py`, `diagnostics.py`, `viz.py`, `validation.py`, `__init__.py`, `ontology/amt.ttl`, `py/site_howto.py` (drei Einträge: `AMT-E104`, `AMT-W205`, `AMT-N303`), `py/step_determinism.py` (Probe `hextuple-demo.ttl`), `README.md`, `CHANGELOG.md`.
- Gemessen: die Kantenmenge (Rolle, Quelle, Ziel, Gewicht, `inferred`, `provenance`) ist für alle bisherigen Beispiele gegenüber 0.5.0 gleich (Vergleich der JSON-Listen, nicht der Dateien); alle Tests aus 0.5.0 laufen unverändert; die Ausgabe jedes Beispiels besteht jetzt die Shapes (Befund vom 2026-10-30 behoben, `xsd:decimal`).
- Beim Testen gefunden und behoben: Turtle-Text als String statt Pfad ließ `load_amt` und `validate_against_shapes` abstürzen (A4, „Eingabe als Text“).
- Nicht geprüft: Python 3.10 unter Windows (nur 3.13 hier; der Code nutzt `X | None` mit `from __future__ import annotations` und keine Backslashes in f-Strings).
- Offen: `fw:EqualShareRule` und `fw:PropagationMethod` sind in `amt.ttl` nur genannt, nicht definiert (die Definition liegt in der FW-Ontologie, D16).

### S22 – Hextupel im JS-Port und im Explorer

**Ziel:** Der Explorer rechnet und zeigt dasselbe wie die Python-Engine.

**Inhalt:** `docs/js/amt-reasoner.js` bekommt Typ, Methode und die Kombinationsregel (Änderungen an der Python-Logik ziehen den Port nach, A4 vom 2026-10-26); `tests/test_js_reasoner.py` vergleicht beide auch für `type` und `method`; der Explorer zeigt Typ und Methode im Kanten-Tooltip und lädt `hextuple-demo.ttl` in der Beispielliste. Die Kopie im Playground (`leiza-rse/amt-playground`) folgt als eigener Patch dort.

**Abnahme:** der Paritätstest ist grün (Node vorhanden), `tests/test_offline.py` bleibt grün, im Explorer zeigt `hextuple-demo` Typ und Methode an abgeleiteten und behaupteten Kanten.

### Erledigt 2026-10-30

- `docs/js/amt-reasoner.js`: `effectiveType`, `storedType`, `combineTypes`, Typ und Methode beim Ableiten, derselbe Gleichstandsschlüssel; `docs/js/amt.js` liest `fw:hasType`, `fw:hasMethod` und `fw:hasDegreeOfConnection`; `amt-render.js` zeigt Typ und Methode im Kanten-Tooltip; `amt-export.js` und der RDF-Dialog schreiben `xsd:decimal`, `fw:hasType`, `fw:hasMethod`, Cypher bekommt `type` und `method`.
- `tests/test_js_reasoner.py` vergleicht jetzt auch `type` und `method` (alle Beispiele, drei Fälle im Demo, `combineTypes`, Gleichstand). Im Headless-Browser geprüft (Playwright, Seite `explorer/?ttl=data/hextuple-demo.ttl`): acht behauptete und fünf abgeleitete Kanten mit dem erwarteten Tooltip, keine Konsolenfehler; dieser Browser-Test ist nicht Teil von `main.py`.
- Die Beispielliste des Explorers entsteht aus `examples/`; `hextuple-demo` steht darin, ohne weitere Änderung.
- Offen: die Kopie im Playground (`leiza-rse/amt-playground`) folgt als eigener Patch dort.

### S23 – Runner und Release 0.6.0 / 0.5.0

**Ziel:** Hextupel-Dateien laufen über den Runner, beide Repos sind veröffentlicht und bei Zenodo archiviert.

**Inhalt:** nach dem Muster von S18: 23a (Patch) Versionen in `pyproject.toml`, `amt/__init__.py`, `CITATION.cff`, `py/amt_dev_utils.py`, `CHANGELOG.md` (Engine 0.6.0; Runner 0.5.0 in `run_amt.py`, `CITATION.cff`, `py/amt_runner_dev_utils.py`, `CHANGELOG.md`); im Runner das Beispiel samt `.md`, ein README-Abschnitt und der Hinweis, dass Typ und Methode die Engine 0.6.0 brauchen (`--update`); 23b (manuell) Tag, GitHub-Release, Zenodo; 23c (Patch) Versions-DOIs.

**Abnahme:** wie S18: `python main.py --strict` zweimal grün in beiden Repos, `git status` sauber, `python main.py --only smoke --strict` im Runner gegen die Engine `main`, Tags und Releases sichtbar, Versions-DOIs nach 23c in der README.

## Teil D – Offene Punkte

- **D1** Autorenliste: erledigt in S3 (2026-10-26), siehe A4.
- **D2** erledigt in S9: `amt.ttl` ist eine Obermenge der Fassung von 2018; die Veröffentlichung wird aus `amt.ttl` erzeugt.
- **D9** erledigt in S14: Namensgeschichte in der Fassung B (A4, 2026-10-27).
- **D3** erledigt in S7: Ursache liegt in pyshacl und rdflib, die zwei Meldungen sind gefiltert.
- **D7** erledigt in S7: Verstöße sind sortiert.
- **D4** erledigt in S7: siehe A4 („Verhältnis zu `amt-explore`“).
- **D5** erledigt in S7: Standard-Ref des Runners bleibt `main` (A4).
- **D8** erledigt in S10: Ursache war `Dataset.contexts is deprecated` (rdflib 7.6, ausgelöst von pyshacl 0.26.0), jetzt gefiltert. Vorher: Unter Windows meldet `pytest` 63 Tests mit 204 Warnungen (Linux: keine). Offen: `python -m pytest tests -q -rw` in `C:\git\amt-engine` ausführen, die Warnungsarten ablesen und entscheiden, ob sie zu filtern oder zu beheben sind.
- **D10** Gestaltung: Farbwelt und Logos umgesetzt in S11c (`design/palette.yaml`). Wortlaut des Familien-Abschnitts erledigt in S14, Links bewusst keine (Alpaka und Alligator in Überarbeitung). Schrift erledigt in S15 (Roboto, lokal). Offen: vektorisierte Logos (die Logos der Institutionen bleiben bis auf Weiteres Pixelbilder; Pinguin, Alpaka und Alligator sind eigene Entwürfe des Autors, erstellt mit Google Gemini). Der Explorer startet seit S11c mit `animals.ttl`.
- **D11** Der Playground (`leiza-rse/amt-playground`) und der Explorer sind funktional fertig, dürfen aber später schöner und hübscher werden (Layout, Aufteilung, Startnetz mit echten Beispieldaten); der Playground bleibt im LEIZA-Blau.
- **D6** Exit-Code des Runners bei Konsistenzverletzungen: heute immer 0. Wer den Runner in Skripten oder CI nutzt, kann Verletzungen nur am Text der Ausgabe erkennen. Entscheidung (2026-10-26): vorerst unverändert; falls geändert, dann als eigener Schritt mit Test, CHANGELOG-Eintrag und Versionsentscheidung.
- **D12** Weitere How-To-Unterseiten (Rezepte: Rollen und Axiome Schritt für Schritt, AMT-Datei aus Wikibase/Wikidata; „Ergebnis lesen“ ist mit S17 erledigt) und ein Beispiel `examples/afe-coins.ttl` mit dem AFE-Fall; wartet auf Rückmeldung von Karsten und Lasse, ob das Rezept auf `howto/create/` für ihre Daten reicht.
- **D13** erledigt in S20 (2026-10-30): `fw:derivedFrom` und der Evidenzknoten werden gelesen und unverändert durchgereicht, abgeleitete Kanten bekommen kein `fw:derivedFrom` (A4). Die FW-Definition verlangt bei abgeleiteten Aussagen einen Verweis auf die Antezedens-Aussagen; das braucht stabile IRIs statt Blank Nodes und bleibt ein möglicher späterer Schritt.
- **D14** erledigt in S20 (2026-10-30): Inverse und Subsumption ohne Methode, mit dem Typ der Quellkante; bei Mehrfachableitung entscheidet der Weg mit dem höchsten Gewicht, bei Gleichstand die kleinste Methoden-IRI (A4).
- **D15** erledigt in S20 (2026-10-30): `xsd:decimal` in der Turtle-Ausgabe (A4); die Ausgabe jedes Beispiels ändert sich einmalig und wird im CHANGELOG von S21 genannt.
- **D16** Rückmeldung an die FW-Ontologie (Repo gehört dem Autor, eigener Patch dort): (a) die Kombinationsregel für Typen abgeleiteter Aussagen, (b) die AMT-Logiken stehen jetzt in `amt.ttl`, `data/amt-alignment.ttl` kann entfallen, (c) `fw:implementedBy` für `fw:EqualShareRule`, (d) dass in AMT jede Aussage ohne Angabe als vage gilt, steht dort nirgends.
- **D17** Mini-AMT-Repo (`leiza-scit/CHNT2026-amt`): die Zuordnung „sichere Aussage, kein Typ“ in `weights.py` entfällt mit dem Standard „vage“; dort in S3a mitnehmen. Der Schritt „Hextupel in amt-engine und amt-runner“ im Primer jenes Repos entspricht S20 bis S23 hier.
- **D18** teilweise erledigt in S19 (2026-10-30): Pages-Adresse `https://alpaca-fair-framework.github.io/amt-engine/` geprüft, `deploy/redirects.yaml` umgestellt (A4). Stand 2026-10-30 laut Autor: `.htaccess` angepasst und Zenodo umgestellt; ungeprüft bleibt `py/check_redirects.py`. Ursprünglich offen, durch den Autor: die erzeugte `.htaccess` für `academic-meta-tool.xyz` per FTP neu hochladen; einen neuen Pull Request in `perma-id/w3id.org` stellen (ein bestehender Eintrag zeigt, falls #6998 gemergt ist, noch auf die alte Pages-Adresse; Stand nicht geprüft); die Zenodo-Anbindung an der neuen Organisation prüfen (die Concept-DOIs bleiben); danach `python py/check_redirects.py`.
