"""
AMT.engine — Academic Meta Tool reasoning engine.

A pure-Python implementation of the AMT framework with:

* SHACL pre-validation of input files
* n-ary RoleChainAxioms (legacy 2-ary form still supported)
* Six fuzzy-logic operators (Goedel, Product, Lukasiewicz, Einstein,
  Geometric Mean, Hamacher) via a unified registry-based aggregator
* Provenance tracking on inferred edges
* Four export formats: RDF/Turtle, Neo4J Cypher, two-file CSV, and a
  self-contained interactive HTML graph

Usage in three flavours from one codebase:

1. **As a library** – ``from amt import load_amt, do_reasoning, export_ttl``
2. **From the command line** – ``amt input.ttl --reason --validate --export-ttl out.ttl``
3. **Full pipeline in one call** – ``from amt.runner import run_all; run_all("input.ttl")``

See ``README.md`` for examples.
"""
from .core import (
    load_amt,
    local_name,
)
from .reasoning import (
    check_consistency,
    do_reasoning,
)
from .logic import (
    LOGIC_REGISTRY,
    aggregate_weights,
    get_arity,
    is_parametrised,
    GOEDEL,
    PRODUCT,
    LUKASIEWICZ,
    EINSTEIN,
    GEOMETRIC,
    HAMACHER,
)
from .validation import (
    AMTValidationError,
    ValidationResult,
    validate_against_shapes,
)
from .export import (
    export_csv,
    export_cypher,
    export_ttl,
    write_cypher,
    write_ttl,
)
from .viz import (
    build_network,
    render_to_html,
    show_in_notebook,
)

__version__ = "0.2.0"

__all__ = [
    # core
    "load_amt",
    "local_name",
    # reasoning
    "do_reasoning",
    "check_consistency",
    # logic
    "aggregate_weights",
    "get_arity",
    "is_parametrised",
    "LOGIC_REGISTRY",
    "GOEDEL",
    "PRODUCT",
    "LUKASIEWICZ",
    "EINSTEIN",
    "GEOMETRIC",
    "HAMACHER",
    # validation
    "validate_against_shapes",
    "AMTValidationError",
    "ValidationResult",
    # export
    "export_ttl",
    "export_cypher",
    "export_csv",
    "write_ttl",
    "write_cypher",
    # viz
    "build_network",
    "render_to_html",
    "show_in_notebook",
    # meta
    "__version__",
]
