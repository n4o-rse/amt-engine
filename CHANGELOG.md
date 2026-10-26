# Changelog

All notable changes to AMT.engine are documented in this file.

The format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/)
and the project uses [Semantic Versioning](https://semver.org/).

The repository carries no git tags. The entries for 0.1.0 to 0.3.0 were
reconstructed from the commit history; each date is that of the commit that
introduced the version number in `pyproject.toml`.

## [Unreleased]

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
- The CI workflow uses `actions/checkout@v5`, `actions/setup-python@v6` and
  `actions/upload-artifact@v5`, which run on Node 24.
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

[Unreleased]: https://github.com/n4o-rse/amt-engine/compare/a50822c...HEAD
[0.3.0]: https://github.com/n4o-rse/amt-engine/commit/03eb093
[0.2.0]: https://github.com/n4o-rse/amt-engine/commit/5cc2fbf
[0.1.0]: https://github.com/n4o-rse/amt-engine/commit/3357cde
