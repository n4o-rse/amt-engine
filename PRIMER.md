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
- Die Historie hat 30 Commits und keine Tags. Die Versionen stehen nur in `pyproject.toml`: 0.1.0 (2026-04-28), 0.2.0 (2026-05-05), 0.3.0 (2026-08-29).
- Commit `db1db2d` (2026-05-04) führt den Verlauf von `amt-explore` in dieses Repo zusammen. Der Webviewer in `docs/` stammt von dort.
- Windows-Lauf von `python main.py` (2026-10-26, `C:\git\amt-engine`): alle sechs Schritte `ok`, 62 Tests grün in 16,4 s, Gesamtlauf 38,1 s. Der Determinismus-Test besteht auch dort. Die Warnungszahl im Testlauf liegt mit 15 006 weit unter dem Linux-Wert (rdflib- und Python-Version, siehe D3).
- `docs-sync` meldete auf Windows fünf Dateien als `updated`, obwohl die Blobs in `examples/` und `docs/data/` identisch sind und überall nur LF enthalten (geprüft an `9a0e8b7`). Ursache: `core.autocrlf` macht im Working Tree CRLF daraus; der Byte-Vergleich sah Unterschiede, wo keine sind. Behoben in S1a.
- `examples/skos-mapping-example.ttl` meldet beim Konsistenzcheck zwei Verletzungen (`exactMatch` und `questionableMatch` zum selben Ziel; Selbstschleife über `questionableMatch`). Das ist als Demo gewollt (A4). Der Runner beendet sich trotzdem mit Exit-Code 0, deshalb bleibt der Schritt `examples` auf `ok`.
- `pyproject.toml` nennt als Autor „AMT contributors"; `LICENSE` nennt Florian Thiery | LEIZA | NFDI4Objects; `docs/index.htm` nennt Thiery und Unold (Software) sowie Thiery und Mees (Datenkonzept).

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
| Autoren in `CITATION.cff` | nur Florian Thiery, ohne ORCID, bis die Liste geklärt ist | Vorschlag 2026-10-26 |
| Bedeutung von `RELEASE_DATE` | Datum des Commits, der die Version gesetzt hat (0.3.0: 2026-08-29) | Vorschlag 2026-10-26 |

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
| S2 | `amt-runner` auf das Muster: `PRIMER.md`, `CHANGELOG.md`, `CITATION.cff`, `requirements.txt`, Dev-Pipeline | amt-runner | S1 | offen |
| S3 | `CITATION.cff` klären: Autorenliste, ORCID, Rolle von Unold und Mees | amt-engine, amt-runner | S1 | offen |
| S4 | CI: GitHub Action mit `python main.py --strict` bei Push und Pull Request | amt-engine | S1 | offen |
| S5 | Tags `v0.1.0` bis `v0.3.0` setzen, Releases, Zenodo-DOI | amt-engine | S3 | offen |

Unabhängig voneinander laufen können S2, S3 und S4; nur S5 wartet auf die Autorenliste aus S3. Der Runner (S2) liest die Engine zur Laufzeit aus `main`; er braucht S5 erst, wenn er auf Tags pinnen soll.

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
- Offen bleibt nur, dass Windows den Fix noch nicht gesehen hat. Erster Lauf dort: `python main.py --strict`, danach `git status --short`.

---

## Teil D – Offene Punkte

- **D1** Autorenliste: Unold und Mees stehen im Webviewer, nicht in `pyproject.toml`. Entscheidung gehört in S3 und sollte als Formular gefragt werden.
- **D2** Wo wird `http://academic-meta-tool.xyz/vocab#` aufgelöst, und liegt die Ontologie dort in derselben Fassung wie `ontology/amt.ttl`?
- **D3** Die rund 83 700 rdflib-Warnungen im Testlauf: Ursache klären (eigener Code oder Bibliothek) und, falls eigener Code, beheben.
- **D4** Verhältnis zu `amt-explore`: Der Verlauf ist seit 2026-05-04 hier eingemergt. Wird das separate Repo weitergepflegt, oder ist `docs/` hier jetzt maßgeblich?
- **D5** Ob der Runner künftig auf Tags statt auf `main` pinnt, hängt an S5.
- **D6** Exit-Code des Runners bei Konsistenzverletzungen: heute immer 0. Wer den Runner in Skripten oder CI nutzt, kann Verletzungen nur am Text der Ausgabe erkennen. Entscheidung (2026-10-26): vorerst unverändert; falls geändert, dann als eigener Schritt mit Test, CHANGELOG-Eintrag und Versionsentscheidung.
