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
- `pytest` meldet 62 grüne Tests und rund 83 700 Warnungen (rdflib-Deprecation; die Zahl schwankt leicht zwischen Läufen); die Warnungen verdecken jede andere Meldung.
- `.gitignore` schließt `dist/` aus (setuptools-Ausgabe). Das Primer-Muster legt Produkte sonst in `dist/` ab; hier geht das nicht, siehe A4.
- Die Historie hatte 30 Commits und keine Tags. Die Versionen standen nur in `pyproject.toml`: 0.1.0 (2026-04-28), 0.2.0 (2026-05-05), 0.3.0 (2026-08-29). Seit S5 tragen die Commits `3357cde`, `5cc2fbf` und `03eb093` die Tags `v0.1.0` bis `v0.3.0`.
- Commit `db1db2d` (2026-05-04) führt den Verlauf von `amt-explore` in dieses Repo zusammen. Der Webviewer in `docs/` stammt von dort.
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
  meta ─► ontology ─► tests ─► examples ─► determinism ─► docs-sync
        │
        ▼
build/pipeline_report.txt        docs/data/*.ttl (Spiegel von examples/)
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
| Versionen der GitHub Actions | Hauptversionen mit Node 24: `checkout@v5`, `setup-python@v6`, `upload-artifact@v5`; bei der nächsten Node-Warnung erneut prüfen | 2026-10-26 |
| Standard-Ref des Runners | `amt-runner` zeigt weiter auf `main`; ein Pin auf Tags kommt erst nach S5 | 2026-10-26 |
| Autoren in `CITATION.cff` und `pyproject.toml` | Florian Thiery (ORCID 0000-0002-3246-3531) und Allard W. Mees (ORCID 0000-0002-7634-5342), beide LEIZA; ersetzt den Vorschlag „nur Thiery“ | 2026-10-26 |
| Rechteinhaber in `LICENSE` | „Florian Thiery \| LEIZA \| Research Squirrel Engineers Network“, in beiden Repos gleich; `docs/LICENSE` und `docs/js/LICENSE` bleiben unverändert (Dritt- und Altbestand) | 2026-10-26 |
| CI-Matrix | Ubuntu und Windows, Python 3.10 und 3.13; Auslöser Push auf `main`, Pull Request und manuell; `python main.py --strict`; Report als Artefakt | 2026-10-26 |
| Rolle von Unold | kein Autor von AMT.engine; das ursprüngliche Academic Meta Tool (Unold, Thiery, 2017) steht unter `references` in `CITATION.cff`, ohne erfundene DOI | 2026-10-26 |
| Bedeutung von `RELEASE_DATE` | Datum des Commits, der die Version gesetzt hat (0.3.0: 2026-08-29, 0.3.1: 2026-10-26) | 2026-10-26 |
| Tags und Releases | `v0.1.0` bis `v0.3.0` als annotierte Tags auf den Commits aus dem CHANGELOG, ohne GitHub-Release; `v0.3.1` ist das erste Release (Version 0.3.1: keine Verhaltensänderung, nur Metadaten, Tooling, CI) | 2026-10-26 |
| DOI | Concept-DOI `10.5281/zenodo.23669466` steht in `CITATION.cff` und README; Version 0.3.1 trägt `10.5281/zenodo.23669467` | 2026-10-26 |
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

---

## Teil D – Offene Punkte

- **D1** Autorenliste: erledigt in S3 (2026-10-26), siehe A4.
- **D2** Wo wird `http://academic-meta-tool.xyz/vocab#` aufgelöst, und liegt die Ontologie dort in derselben Fassung wie `ontology/amt.ttl`?
- **D3** Die rund 83 700 rdflib-Warnungen im Testlauf (Linux, Python 3.13; auf Windows mit Python 3.10 sind es 15 006): Ursache klären (eigener Code oder Bibliothek) und, falls eigener Code, beheben.
- **D7** Die Reihenfolge der vier Verstöße in der Konsolenausgabe des Ontologie-Schritts (`example-invalid.ttl`) ist bei jedem Lauf anders (pyshacl). Die geprüften Ausgabedateien sind davon nicht betroffen, der Determinismus-Schritt ist grün. Sortieren wäre ein kleiner eigener Schritt.
- **D4** Verhältnis zu `amt-explore`: Der Verlauf ist seit 2026-05-04 hier eingemergt. Wird das separate Repo weitergepflegt, oder ist `docs/` hier jetzt maßgeblich?
- **D5** Ob der Runner künftig auf Tags statt auf `main` pinnt: mit `v0.3.1` gibt es jetzt einen Tag, die Entscheidung kann fallen. Bis dahin bleibt `main` (A4).
- **D6** Exit-Code des Runners bei Konsistenzverletzungen: heute immer 0. Wer den Runner in Skripten oder CI nutzt, kann Verletzungen nur am Text der Ausgabe erkennen. Entscheidung (2026-10-26): vorerst unverändert; falls geändert, dann als eigener Schritt mit Test, CHANGELOG-Eintrag und Versionsentscheidung.
