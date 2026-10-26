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
- `pyproject.toml` nannte als Autor „AMT contributors"; `LICENSE` nannte Florian Thiery | LEIZA | NFDI4Objects; `docs/index.htm` nennt Thiery und Unold (Software) sowie Thiery und Mees (Datenkonzept). Geklärt in S3 (A4).

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
| Release 0.4.0 | erst am Ende (nach S13); die ungereleasten Änderungen aus S7 bis S13 gehören dazu | 2026-10-26 |
| Zenodo | GitHub-Zenodo-Anbindung ist für beide Repos eingeschaltet; jedes GitHub-Release erzeugt eine Version mit DOI, ein bloßer Tag nicht; deshalb keine Releases für alte Versionen | 2026-10-26 |

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
| S12 | w3id-Eintrag und Umleitung des FTP (`.htaccess`) auf GitHub Pages | amt-engine | S9, S10 | offen |
| S13 | D6 (Exit-Code) und Release 0.4.0 samt Zenodo | amt-engine, amt-runner | S10 bis S12 | offen |

S3, S4, S5 und S6 sind erledigt. Offen bleiben die Punkte in Teil D. Der Runner (S2) liest die Engine zur Laufzeit aus `main`; er braucht S5 erst, wenn er auf Tags pinnen soll.

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

---

## Teil D – Offene Punkte

- **D1** Autorenliste: erledigt in S3 (2026-10-26), siehe A4.
- **D2** erledigt in S9: `amt.ttl` ist eine Obermenge der Fassung von 2018; die Veröffentlichung wird aus `amt.ttl` erzeugt.
- **D9** Startseite (S10): die Geschichte hinter dem Namen („Wir wollten erst ein Amt errichten, das arbeitet …“) im Wortlaut vom Autor; bis dahin steht nur ein vorsichtiger Entwurf.
- **D3** erledigt in S7: Ursache liegt in pyshacl und rdflib, die zwei Meldungen sind gefiltert.
- **D7** erledigt in S7: Verstöße sind sortiert.
- **D4** erledigt in S7: siehe A4 („Verhältnis zu `amt-explore`“).
- **D5** erledigt in S7: Standard-Ref des Runners bleibt `main` (A4).
- **D8** erledigt in S10: Ursache war `Dataset.contexts is deprecated` (rdflib 7.6, ausgelöst von pyshacl 0.26.0), jetzt gefiltert. Vorher: Unter Windows meldet `pytest` 63 Tests mit 204 Warnungen (Linux: keine). Offen: `python -m pytest tests -q -rw` in `C:\git\amt-engine` ausführen, die Warnungsarten ablesen und entscheiden, ob sie zu filtern oder zu beheben sind.
- **D10** Gestaltung (angekündigt am 2026-10-26, noch nicht umgesetzt): eigene Farbwelt für das AMT, getrennt vom LEIZA-Forschungsblau (das beim leiza-Playground bleibt); neue Logos (auch das neue AMT-Logo) liefert der Autor für die Startseite; der Explorer startet mit dem Beispiel `animals.ttl`, das erleichtert das Erklären.
- **D6** Exit-Code des Runners bei Konsistenzverletzungen: heute immer 0. Wer den Runner in Skripten oder CI nutzt, kann Verletzungen nur am Text der Ausgabe erkennen. Entscheidung (2026-10-26): vorerst unverändert; falls geändert, dann als eigener Schritt mit Test, CHANGELOG-Eintrag und Versionsentscheidung.
