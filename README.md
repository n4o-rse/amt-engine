# amt – Academic Meta Tool, Python edition

A pure-Python port of the [Academic Meta Tool](http://academic-meta-tool.xyz/),
originally written in JavaScript (N3.js + vis.js). Same data model, same fuzzy
logic operators, same export formats — usable from a notebook, from a script,
or as a backend for the existing webviewer.

## Install

```bash
pip install -e .                  # core only
pip install -e ".[notebook]"      # + ipywidgets, pandas, ipython
pip install -e ".[dev]"           # + pytest
```

Requires Python ≥ 3.10. Core dependencies: `rdflib`, `pyvis`.

## Quick start

The fastest way to see what AMT does with your TTL file:

```bash
python -m amt.runner examples/SKOSconceptExample.ttl
```

This runs the full pipeline (load → info → consistency check → reasoning →
exports) and writes three files to `examples/out/`:

- `SKOSconceptExample.reasoned.ttl` — Turtle with inferred edges
- `SKOSconceptExample.cypher` — Neo4J Cypher
- `SKOSconceptExample.html` — standalone interactive graph

Open the `.html` file in a browser to explore the graph.

## Three ways to use it

### 1. As a library

```python
from amt import load_amt, do_reasoning, check_consistency, export_ttl

amt = load_amt("examples/SKOSconceptExample.ttl")

print(len(amt["concepts"]), "concepts,", len(amt["edges"]), "edges")

reasoned = do_reasoning(amt["edges"], amt["axioms"])
ok, violations = check_consistency(amt["edges"], amt["axioms"])

ttl = export_ttl(
    amt["nodes"], amt["edges"], amt["concepts"], amt["roles"],
    amt["axioms"], rdf_graph=amt["graph"], prefix=amt["prefix"],
    with_reasoning=True,
)
```

### 2. From the command line

Two entry points:

**`amt.runner`** — runs the full pipeline with sensible defaults:

```bash
python -m amt.runner examples/SKOSconceptExample.ttl
python -m amt.runner examples/SKOSconceptExample.ttl -o out/
python -m amt.runner examples/SKOSconceptExample.ttl --no-reason --no-check
```

**`amt.cli`** — fine-grained control over individual steps:

```bash
python -m amt.cli examples/SKOSconceptExample.ttl --info --check
python -m amt.cli examples/SKOSconceptExample.ttl --reason \
    --export-ttl    out/skos.ttl     \
    --export-cypher out/skos.cypher  \
    --export-html   out/skos.html
```

Run `python -m amt.cli --help` or `python -m amt.runner --help` for all flags.

> **Running from VS Code on Windows:** open the integrated terminal in the
> project root (`Ctrl+ö` or `View → Terminal`) and use `python -m amt.runner …`.
> Don't run `cli.py` or `runner.py` directly with the green play button —
> the relative imports require module mode (`-m`). For F5 / debugger use,
> add a `launch.json` configuration with `"module": "amt.runner"` instead
> of `"program": …`.

### 3. Feeding the bundled webviewer

The `docs/` folder contains the original JavaScript webviewer. The viewer
**does its own reasoning in the browser** — same fuzzy logic, same axioms —
so for the webviewer use case you only need to publish the **source** TTL,
not a pre-reasoned export:

```bash
# Copy a source TTL into the viewer's data folder
cp examples/SKOSconceptExample.ttl docs/data/

# Serve locally
cd docs && python -m http.server 8000
# open http://localhost:8000/index.htm?ttl=data/SKOSconceptExample.ttl
```

In the viewer you can toggle reasoning on/off to see the difference between
asserted and inferred edges live.

A GitHub Action (`.github/workflows/sync-examples-to-docs.yml`) syncs
`examples/*.ttl` to `docs/data/` automatically on every push to `main`.
The same `docs/` folder is published as a **GitHub Pages site** when Pages
is configured with source `main` / folder `/docs`. See
[`INTEGRATION.md`](INTEGRATION.md) for details.

**When *would* you publish a pre-reasoned export?** Mainly for downstream
tools that don't have AMT's reasoner — Neo4J imports via `--export-cypher`,
or standalone HTML reports for people without webviewer access. For those
cases, point the runner at `docs/data/` directly:

```bash
python -m amt.runner examples/SKOSconceptExample.ttl -o docs/data/
```

## Notebook

The notebook in `notebooks/amt-explore.ipynb` is a thin wrapper around the
library — upload widget, dataframes for inspection, inline pyvis graph,
exporters. All the engine code lives in `amt/`.

## Layout

```
amt/
├── core.py        load_amt, do_reasoning, check_consistency
├── viz.py         build_network, render_to_html, show_in_notebook
├── export.py      export_ttl, export_cypher
├── cli.py         per-step CLI (python -m amt.cli)
└── runner.py      full-pipeline runner (python -m amt.runner)

docs/              JS webviewer (GitHub Pages source)
tests/             pytest smoke tests
notebooks/         interactive exploration
examples/          source TTL files (read-only inputs)
examples/out/      local pipeline outputs (gitignored)
INTEGRATION.md     how Python exports plug into the webviewer
```

## What was ported from the JS side

| JS source            | Python module    |
|----------------------|------------------|
| `amt.js`             | `amt/core.py`    |
| `amt-render.js`      | `amt/viz.py`     |
| `amt-export.js`      | `amt/export.py`  |

Everything is round-trip-compatible with the JS tool: a TTL written by
`export_ttl` can be opened in the webviewer, and a TTL written by the
webviewer can be loaded with `load_amt`.

## License

MIT