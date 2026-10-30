# Changelog

All notable changes to AMT.engine are documented in this file.

The format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/)
and the project uses [Semantic Versioning](https://semver.org/).

The entries for 0.1.0 to 0.3.0 were reconstructed from the commit history;
each date is that of the commit that introduced the version number in
`pyproject.toml`. The tags `v0.1.0` to `v0.3.0` were set afterwards on exactly
those commits. 0.3.1 is the first release published on GitHub and archived on
Zenodo.

## [Unreleased]

## [0.6.0] - 2026-10-30

0.6.0 makes a statement a hextuple: besides its weight it can say what kind of fuzziness the weight expresses
(`fw:hasType`) and how it was obtained (`fw:hasMethod`), with the vocabulary of the FW ontology. A file without
either behaves as in 0.5.0 and has the same edges. The repository now lives under `alpaca-fair-framework`.

### Added

- Type and method of a statement (the hextuple, PRIMER S21/S22). Besides `amt:weight` a statement can carry
  `fw:hasType` (`fw:Vagueness`, `fw:Uncertainty`, `fw:FuzzinessWobbliness`) and `fw:hasMethod` from the FW ontology
  (`http://w3id.org/fw_ontology/`); `fw:derivedFrom` evidence is read and passed through. All are optional: a
  statement without a type is a vagueness statement, also at weight 1.0, and a plain quadruple behaves as in 0.5.0
  (the set of edges of every bundled example is unchanged).
- The weight is read from `amt:weight` and from `fw:hasDegreeOfConnection`; the output uses `amt:weight`.
- Derived statements carry a method and a type: a `RoleChainAxiom` sets the method to its logic and the type to the
  common type of its antecedents (`fw:FuzzinessWobbliness` if they differ); `InverseAxiom` and `SubsumptionAxiom`
  set no method and take the type of the source edge. With several paths, the one with the highest weight decides;
  on equal weights the smaller method IRI.
- New module `amt/fw.py` (`effective_type`, `combine_types`, the three type IRIs); `amt.effective_type`,
  `amt.combine_types` and `amt.DEFAULT_TYPE` are exported. Edge dicts have the keys `type`, `method`, `evidence`.
- Diagnostics `AMT-E104` (conflicting `amt:weight` and `fw:hasDegreeOfConnection`; `amt:weight` is used),
  `AMT-W205` (`fw:hasType` is none of the three types) and `AMT-N303` (type without method), each with an entry on
  the How-To page "check an AMT file".
- `edges.csv` has the columns `type` (effective type) and `method` at the end; Cypher relationships get the
  properties `type` and `method`; the graph tooltip shows both.
- `ontology/amt.ttl`: prefix `fw:`; the six logics are also `fw:PropagationMethod`.
- Explorer (`docs/js/amt-reasoner.js`, `amt.js`): same rules as the Python engine, type and method in the edge
  tooltip and in the Turtle and Cypher export. `tests/test_js_reasoner.py` compares type and method as well.
  Evidence is not carried by the Explorer.
- `examples/hextuple-demo.ttl` and `.md`; `tests/test_hextuple.py`.

### Changed

- A failed import in a step of the development pipeline (`py/step_site.py`) now shows the original error. Before,
  the fallback import hid it behind `'py' is not a package` when the real cause was a missing file or package.
- The Turtle output writes `amt:weight` as `xsd:decimal` instead of `xsd:double` (in Python and in the Explorer
  export), as `amt:WeightShape` requires. Before, the reasoned output of every example failed the shapes (152
  violations for `animals.reasoned.ttl`). The output of every example changes once because of this.
- Derived edges in the Turtle output carry `fw:hasMethod` (the logic that produced them), so `*.reasoned.ttl`
  declares the prefix `fw:` whenever there is a derived edge from a role chain.

- `README.md`, "Citation": names the version DOI of 0.5.0,
  `10.5281/zenodo.23691499`. The concept DOI is unchanged.
- The repository now lives under `alpaca-fair-framework`. Every link to the repository, the issue tracker
  and the GitHub Pages site (`https://alpaca-fair-framework.github.io/amt-engine/`) is updated in
  `CITATION.cff`, `README.md`, the hint texts of `amt-runner`, the site generators and the reference links of
  this file.
- `deploy/redirects.yaml` names the new Pages address and the new repository addresses; the redirect files
  generated from it (`deploy/academic-meta-tool.xyz/.htaccess`, `deploy/w3id/ids/amt/`) lead there. They have
  to be deployed again: the `.htaccess` of `academic-meta-tool.xyz` by FTP, the `w3id.org/amt/` entry by a new
  pull request at `perma-id/w3id.org`.
- The instance namespaces of the bundled examples change from `http://github.com/n4o-rse/amt-explore/` and
  `http://github.com/n4o-rse/amt-engine/subsumption-demo/` to the same paths under `alpaca-fair-framework`;
  the mirror in `docs/data/` and the expected IRIs in the tests follow. Files that use the old namespace still
  load and validate.

### Fixed

- `load_amt` and `validate_against_shapes` raised `OSError: File name too long` when given the text of a larger
  Turtle file instead of a path. Such text is now treated as Turtle.

## [0.5.0] - 2026-10-27

0.5.0 makes a failed run understandable. A file with a problem now ends with a message that
names the IRI and says what to add, not with a traceback, and the website has a How-To section
for building, checking and running a file. The reasoner, the results of a run and the exit
code 0 for consistency violations are unchanged.

### Added

- `amt/diagnostics.py`: plain-language checks that SHACL cannot make, run after loading by
  `amt-runner` and `amt` and available as `amt.diagnose(amt_dict)`. Each finding has a stable
  code, names the IRI it is about and says what to add: `AMT-E101` (an edge end that is not an
  AMT node, because it has no `amt:instanceOf`), `AMT-E102` (`amt:instanceOf` pointing at
  `amt:Concept` itself or at an undeclared concept), `AMT-E103` (a weighted statement with a
  missing part), `AMT-W201` (weight outside [0, 1]), `AMT-W204` (no weighted statement at all),
  `AMT-N301` and `AMT-N302` (notes: undeclared role, unlabelled nodes).
- `amt-runner --check-only`: validate, load and diagnose, then stop; nothing is written.
  `--strict`: a diagnostic error ends the run with exit code 1. `--debug`: show the Python
  traceback of an unexpected error.
- `amt.format_violations()`: SHACL violations rendered with the node they are about and a hint
  on what to add.
- How-To page "Run an AMT file and look at the result" (`docs/howto/run/`): from cloning the runner and
  placing the file to the check, the full run, the files a run writes, reading the graph and loading it into
  the Explorer, with a troubleshooting list. `tests/test_howto.py` checks that its list of output files equals
  what a real run writes.
- The How-To section of the website (`docs/howto/`): how to build an AMT file (including a
  tested SPARQL CONSTRUCT recipe for turning other RDF into AMT), how to check one, and every
  message explained with cause, fix and example. `py/site_howto.py` holds the examples and
  `tests/test_howto.py` runs them. "How-To" is in the navigation and on the start page.
- Roboto, the house typeface of mainzed, as the typeface of the static pages: the
  files are in `docs/vendor/roboto/` (400, 500 and 700; Latin and Latin Extended;
  SIL OFL 1.1) and `docs/assets/site.css` declares them, so the pages show the same
  type on every device and load nothing from a font server. `tests/test_offline.py`
  checks the declarations and the files.

### Changed

- A failed SHACL validation names the node of each violation ("Each Concept must have a label"
  now says which concept), with the property and a hint. The report lists the node too.
- An unexpected error in `amt-runner` ends with a short message and exit code 3 instead of a
  traceback (`--debug` restores the traceback). Exit code 0 for consistency violations is
  unchanged (decision D6).
- The PNG figures are drawn with Roboto Regular and Bold (`design/fonts/`,
  `py/site_fonts.py`) instead of Pillow's default font and a thickened outline for
  bold text. The fonts belong to the key in `docs/assets/figures.json`, so a changed
  typeface redraws the PNGs.
- `README.md`, "Citation": names the version DOI of 0.4.0,
  `10.5281/zenodo.23688518`. The concept DOI is unchanged.
- This changelog: the entry for 0.4.0 has one list each for Added, Changed and
  Fixed (it had grown by accretion and repeated its headings), its introduction
  says what the release changes, and the entry for 0.3.1 states correctly which
  GitHub Actions run on Node 24.

### Fixed

- `amt-runner` no longer stops with `AssertionError: non existent node ...` when an edge ends at
  an IRI that is not an AMT node. The problem is reported up front (`AMT-E101`), and the HTML
  graph draws such IRIs as grey placeholder nodes.

## [0.4.0] - 2026-10-27

0.4.0 changes nothing in the command line of `amt` and `amt-runner` and nothing
in the results of the Python reasoner. The SHACL violations are now listed in a
fixed order, the HTML export works offline and a Windows encoding error is fixed.
The rest is what the project needs to be found, cited and explored: the
vocabulary and the data model as pages generated from `ontology/amt.ttl`, a start
page in English and German, an Explorer that reasons in the browser with a port
of the Python reasoner, the persistent addresses (`https://w3id.org/amt/` and
academic-meta-tool.xyz redirect to the pages), the bibliography, and the colours
and mascots. Nothing is loaded from a CDN any more.

### Added

- Persistent addresses: `deploy/redirects.yaml` and `py/site_redirects.py`
  generate the `.htaccess` for academic-meta-tool.xyz (the vocabulary `/vocab` is
  negotiated: Turtle, RDF/XML, JSON-LD or the HTML page) and the entry for
  `https://w3id.org/amt/` with its README, both in `deploy/`.
  `py/check_redirects.py` compares the live servers with the file.
- Start page `docs/index.html` (`py/site_home.py`), in English and German with a
  language switch and the light/dark theme: what AMT can and cannot do, a worked
  example, the history (mainzed with i3mainz, Hochschule Mainz and the RGZM, today
  LEIZA; continued in NFDI4Objects, DFG project number 501836407), citation.
- Vocabulary and ontology pages in `docs/vocab/` and `docs/ontology/`, generated by
  a new step `site` of `python main.py` from `ontology/amt.ttl`: every class,
  property, fuzzy logic and reasoning rule with label, comment, domain and range;
  the data model with a validated Turtle example per building block. The
  vocabulary is also published as `amt.ttl`, `amt.rdf` and `amt.jsonld`. The
  namespace `http://academic-meta-tool.xyz/vocab#` is unchanged; every term of the
  2018 vocabulary is still defined.
- Figures drawn from code (`py/site_figures.py`) as SVG and PNG, in the style of
  the 2018 diagrams; the overview of the vocabulary is built from `amt.ttl`.
- Bibliography page `docs/bibliography/`: works that use or describe AMT, in APA 7
  style with the BibTeX of each entry, generated from `data/bibliography.bib`
  (`py/site_bib.py`); the BibTeX file is offered for download.
- `CITATION.cff` names the ZfdG article (Unold, Thiery and Mees, 2019) as the
  `preferred-citation`. The Zenodo DOI `10.5281/zenodo.23669466` (all versions)
  is in `CITATION.cff`, and `README.md` has a "Citation" section with the DOI
  badge. Release 0.3.1 is archived as `10.5281/zenodo.23669467`.
- `design/palette.yaml`, the colour palette of AMT (green, bronze-gold and steel
  blue, taken from the mascots), and `py/site_palette.py`, which generates
  `docs/assets/palette.css`, the palette picture `docs/assets/img/palette.svg|png`
  and the fallback colours of the figures from it. PyYAML joins the development
  requirements.
- The penguin, the alpaca and the alligator on the pages: the penguin in the
  header bar, on the start page and in the Explorer, a new "Part of a family"
  section on the start page, the partner logos in the footer.
- Light and dark theme with a switch on the new pages.
- Explorer: a list of all examples (`docs/data/examples.json`, written by the step
  `docs-sync`) and "load a Turtle file" from the visitor's computer; a status
  line shows whether the loaded graph is consistent, with the violations as a
  tooltip, and a load error is shown instead of an empty graph.
- `docs/vendor/`: the libraries of the Explorer (N3.js, vis, jQuery, jQuery UI,
  Materialize, Material Icons) with their licences.
- `ontology/amt.ttl`: creators, creation date, licence (CC BY 4.0, as published in
  2018) and the source article (Unold, Thiery, Mees 2019) on the ontology resource.
- Tests: for the pages and figures (`tests/test_site.py`, `tests/conftest.py`),
  for the order of the violations, and `tests/test_offline.py` (no page or
  stylesheet loads anything from another server, and every local link and file
  reference resolves). `Pillow` is a development dependency (`requirements.txt`,
  extra `dev`).

### Changed

- The Explorer reasons with `docs/js/amt-reasoner.js`, a port of the Python
  reasoner (`amt/reasoning.py`, `amt/logic.py`): n-ary role chains
  (`amt:antecedents`), subsumption, all six fuzzy logics and `amt:logicParameter`,
  provenance, and the same consistency messages. The old code knew three logics
  and chains of two steps only, so the reasoning showed nothing on the Potter
  example. `tests/test_js_reasoner.py` runs both implementations on every
  bundled example and on a grid of weights. The same file is the source of the copy
  in `leiza-rse/amt-playground`, which now reasons with it and no longer needs a
  triplestore.
- The Explorer no longer loads anything from a CDN, starts with the `animals`
  example and moves to `docs/explorer/`. `docs/index.htm` stays as a redirect that
  keeps `?ttl=` and `#`; relative `?ttl=` paths are resolved from `docs/`, so
  `.../explorer/?ttl=data/animals.ttl` works.
- Explorer layout and look: one slim bar with the dataset title, the consistency
  status, the legend and four buttons instead of the large information boxes. The
  reasoning switch is a labelled button ("Reasoning: off/on"), grey when off and
  red, the colour of the inferred edges, when on (it was blue and red without a
  meaning). The logos moved from the bar into a box at the bottom right that
  names the origin: a mainzed project of i3mainz and the RGZM (today LEIZA),
  developed further in NFDI4Objects, funded by the DFG, project number 501836407.
  The same sentence is in the footer of every generated page.
- The Turtle and Cypher exports of the Explorer write n-ary chains as RDF lists
  and add `amt:provenance` (Cypher: `provenance`) to inferred statements, as the
  Python exports do.
- The HTML export of the library (`render_to_html`, `amt --export-html`) embeds
  the visualisation library and no longer links Bootstrap, so it works offline;
  `cdn_resources="remote"` restores the small file that loads from a CDN.
- All pages, the figures and the Explorer use the new colours, in the light and
  in the dark theme; inferred edges stay red, asserted edges are steel blue, the
  reasoning switch is bronze when on.
- Start page: the story of the name (the name only works in German) and the
  sentence about the Alpaka Research Framework have their final wording. The
  footer of every page shows the logos of mainzed, i3mainz, LEIZA, NFDI4Objects,
  NFDI and DFG, linked.
- The header of the w3id.org entry lists the addresses, the namespace note and
  the contact and is generated from `deploy/redirects.yaml`. The public address is
  `https://w3id.org/amt/` (the `ids/` is only the folder in the registry).
- SHACL violations are returned and printed in a fixed order (sorted by focus
  node, path and message) by `validate_against_shapes`, the command line and
  `ontology/validate_examples.py`. pyshacl lists them in an order that differs
  between runs and platforms. The set of violations is unchanged.
- `python main.py` runs `docs-sync` and then `site` before `tests`, so everything
  the tests read, and the link test, see the regenerated files.
- `pyproject.toml`: `[tool.pytest.ini_options]` silences two rdflib deprecation
  warnings that pyshacl triggers about 83 000 times per test run, and
  `Dataset.contexts is deprecated` (rdflib 7.6, triggered by pyshacl 0.26.0; it
  showed as 214 warnings on Windows). Other warnings stay visible.
- `actions/upload-artifact` goes from v5 to v6 in the workflow files. v5 still
  runs on Node 20 and made every run print the Node 20 deprecation warning;
  v6 runs on Node 24.

### Fixed

- `render_to_html` (and with it `amt --export-html` and the runner) failed on
  Windows with a `UnicodeEncodeError`: pyvis writes the file in the platform's
  encoding (cp1252), which cannot hold the embedded library. The page is now
  rendered by the engine and written as UTF-8 with LF line ends on every platform.
- The order of `docs/data/examples.json` no longer depends on the platform:
  `docs-sync` sorted `Path` objects, which Windows orders case-insensitively
  and Linux does not, so the manifest and the test that compares it disagreed
  on Windows. It is sorted by lower-case name now.

## [0.3.1] - 2026-10-26

0.3.1 changes no behaviour of the reasoner or the commands `amt` and
`amt-runner`. It adds the development pipeline, citation metadata and
continuous integration.

### Added

- `PRIMER.md`: German work plan with the standing rules, the decisions taken
  so far (Beschlusslage) and the numbered steps for this repository.
- `main.py` and `py/`: a development pipeline with the steps `meta`,
  `ontology`, `tests`, `examples`, `determinism` and `docs-sync`
  (`--list`, `--only`, `--from`, `--skip`, `--dry-run`, `--strict`). The
  product commands `amt` and `amt-runner` are unchanged.
- `.github/workflows/ci.yml`: runs `python main.py --strict` on push to
  `main` and on pull requests, on Ubuntu and Windows with Python 3.10 and 3.13,
  and keeps `build/pipeline_report.txt` of each job as an artefact.
- `CITATION.cff` so the software can be cited. It names Florian Thiery and
  Allard W. Mees as authors, with their ORCIDs, and lists the original
  Academic Meta Tool (Martin Unold and Florian Thiery, 2017) under
  `references`.
- This changelog.

### Changed

- `requirements.txt` now also lists `pytest`; `requirements-dev.txt` is gone, so
  the repository has a single requirements file. `pip install -e ".[dev]"` is
  unchanged. amt-runner installs this file when it clones the engine, so it
  now installs `pytest` as well.
- The CI workflow uses `actions/checkout@v5` and `actions/setup-python@v6`,
  which run on Node 24, and `actions/upload-artifact@v5`, which still runs on
  Node 20 (moved to v6 in 0.4.0).
- `pyproject.toml`: the package authors are Florian Thiery and Allard W. Mees
  instead of "AMT contributors".
- `LICENSE`: the copyright holder reads "Florian Thiery | LEIZA | Research
  Squirrel Engineers Network" (was "... | NFDI4Objects"). The licences in
  `docs/` are third-party or historical and stay as they are.
- `README.md`: describes the development pipeline and lists the new files in
  the layout.

### Fixed

- The `docs-sync` step compares files with line endings normalised. With
  `core.autocrlf` on Windows, identical files differed byte for byte and were
  reported as changed.
- `README.md` pointed to `docs/architecture.mmd`; the Mermaid source lives in
  `amt/architecture.mmd`.
- `docs/data/subsumption-demo.ttl` was missing, although the sync workflow is
  meant to mirror every `examples/*.ttl`. Run `python main.py --only docs-sync`
  to create it.

## [0.3.0] - 2026-08-29

### Added

- Role subsumption: `amt:SubsumptionAxiom` states that one role is a finer
  case of another. The engine computes the transitive closure itself, so only
  the covering relation has to be declared. By default the hierarchy is spelled
  out as entailment; with `minimal=True` (CLI: `--minimal`) an inferred edge is
  dropped when a finer edge relates the same pair at no lower weight. Asserted
  edges are never suppressed, and a coarse relation derived along a strong path
  outranks a fine one derived along a weak path.
- New module `amt/subsumption.py` and `examples/subsumption-demo.ttl` with the
  companion `examples/subsumption-demo.md`.
- `amt/_resources.py`: locates the bundled ontology whether AMT is installed or
  run from a clone.
- `requirements.txt` and `requirements-dev.txt` for environments that vendor the
  source tree instead of installing it (CI images, Docker layers, wrappers such
  as amt-runner).
- Ontology: `amt:SubsumptionAxiom` in `ontology/amt.ttl`, matching shapes in
  `ontology/amt-shapes.ttl`.
- Tests for subsumption (192 added lines in `tests/test_amt.py`).

### Changed

- Axiom types and axiom subjects are iterated in sorted order. Iterating a set
  made rule application order depend on string hashing, which reordered
  provenance lists and left three of the six exported files non-byte-identical
  between runs for no semantic reason.
- Edges are held in a live index keyed by `(role, from, to)` and
  `(role, from)` instead of being rebuilt for every axiom application.
- The runner and the CLI reason once and pass the result to every exporter
  instead of running the fixed point six times.
- The ontology is mapped into the package namespace at build time
  (`package-dir` in `pyproject.toml`), so an installed AMT carries it as
  `amt/ontology/` and no longer claims a top-level `ontology/` directory in
  `site-packages`.

## [0.2.0] - 2026-05-05

### Added

- Pure-Python reasoning engine (`amt/reasoning.py`): fixed-point application of
  role-chain and inverse axioms, with provenance on every inferred edge.
- n-ary `RoleChainAxiom`s through `amt:antecedents` (an RDF list of any length);
  the legacy two-step `antecedent1` / `antecedent2` form is still accepted.
- Six fuzzy-logic operators behind one registry-based `aggregate_weights` API in
  `amt/logic.py`: Goedel, Product, Lukasiewicz, Einstein, Geometric Mean and
  Hamacher.
- SHACL pre-validation of input files against `ontology/amt-shapes.ttl`
  (`amt/validation.py`, dependency `pyshacl`).
- Two-file CSV export (nodes and edges).
- `amt.runner` and the `amt-runner` command: validate, reason, check and
  export in one call, with a Markdown run report.
- `examples/animals.ttl` with `examples/animals.md`, plus the smaller
  `examples/chain-test.ttl` and `examples/skos-mapping-example.ttl`.
- The architecture diagram (`AMT_architecture.png`, `amt/architecture.mmd`).
- `amt/README.md` documenting the package.

### Changed

- `examples/PotterAttributionExample.ttl` and `examples/SKOSconceptExample.ttl`
  updated to the version-2 vocabulary, each with a companion `.md`.
- Package metadata: version 0.2.0 and a dependency on `pyshacl>=0.25`.

## [0.1.0] - 2026-04-28

### Added

- First Python implementation of the Academic Meta Tool: Turtle loader
  (`amt/core.py`), export to Turtle and Neo4J Cypher (`amt/export.py`),
  interactive HTML graph via pyvis (`amt/viz.py`) and the `amt` command
  (`amt/cli.py`).
- The JavaScript webviewer in `docs/` (GitHub Pages), loading a Turtle file
  from the `?ttl=` query parameter, and `INTEGRATION.md` describing how to feed
  it from the Python CLI.
- Example data: `PotterAttributionExample` and `SKOSconceptExample`.
- GitHub Actions workflow `sync-examples-to-docs.yml`, which copies
  `examples/*.ttl` to `docs/data/` on every push to `main`.
- The formal ontology: `ontology/amt.ttl`, `ontology/amt-shapes.ttl`, valid and
  invalid example files, `validate_examples.py` and an ontology README.

[Unreleased]: https://github.com/alpaca-fair-framework/amt-engine/compare/v0.6.0...HEAD
[0.6.0]: https://github.com/alpaca-fair-framework/amt-engine/compare/v0.5.0...v0.6.0
[0.5.0]: https://github.com/alpaca-fair-framework/amt-engine/compare/v0.4.0...v0.5.0
[0.4.0]: https://github.com/alpaca-fair-framework/amt-engine/compare/v0.3.1...v0.4.0
[0.3.1]: https://github.com/alpaca-fair-framework/amt-engine/compare/v0.3.0...v0.3.1
[0.3.0]: https://github.com/alpaca-fair-framework/amt-engine/compare/v0.2.0...v0.3.0
[0.2.0]: https://github.com/alpaca-fair-framework/amt-engine/compare/v0.1.0...v0.2.0
[0.1.0]: https://github.com/alpaca-fair-framework/amt-engine/commit/3357cde
