"""
AMT Fuzzy Logic Operators
=========================

A registry-based implementation of all six fuzzy logic operators recognised
by the AMT ontology. All operators share the same calling convention via
:func:`aggregate_weights`, which takes a list of weights of arbitrary
length n >= 1.

The mapping between operator IRIs and Python implementations is in
:data:`LOGIC_REGISTRY`. Adding a new operator means adding one entry there
and (if appropriate) a matching entry in ``ontology/amt.ttl``.

Binary operators (Goedel, Product, Lukasiewicz, Einstein, Hamacher) are
associative and folded pairwise via :func:`functools.reduce`. The n-ary
operator (Geometric Mean) receives the full weight list at once and
cannot be folded. The :func:`aggregate_weights` API hides this difference
from callers.
"""
from __future__ import annotations

from functools import reduce
from math import prod
from typing import Callable

# ──────────────────────────────────────────────────────────────────────────
# AMT vocabulary IRIs for the six logic operators
# ──────────────────────────────────────────────────────────────────────────
AMT_NS = "http://academic-meta-tool.xyz/vocab#"

GOEDEL       = AMT_NS + "GoedelLogic"
PRODUCT      = AMT_NS + "ProductLogic"
LUKASIEWICZ  = AMT_NS + "LukasiewiczLogic"
EINSTEIN     = AMT_NS + "EinsteinProduct"
GEOMETRIC    = AMT_NS + "GeometricMean"
HAMACHER     = AMT_NS + "HamacherProduct"


# ──────────────────────────────────────────────────────────────────────────
# Pairwise primitives — used to fold binary operators over a list
# ──────────────────────────────────────────────────────────────────────────
def _einstein_pair(x: float, y: float) -> float:
    """Einstein product: (x*y) / (2 - (x+y - x*y))."""
    denom = 2.0 - (x + y - x * y)
    if denom == 0:
        return 0.0
    return (x * y) / denom


def _hamacher_pair(x: float, y: float, gamma: float) -> float:
    """Hamacher product: (x*y) / (gamma + (1-gamma)(x+y - x*y))."""
    denom = gamma + (1.0 - gamma) * (x + y - x * y)
    if denom == 0:
        return 0.0
    return (x * y) / denom


# ──────────────────────────────────────────────────────────────────────────
# Aggregator implementations — each takes (weights, parameter) -> float
# ──────────────────────────────────────────────────────────────────────────
def _agg_goedel(weights: list[float], _param: float | None) -> float:
    return min(weights)


def _agg_product(weights: list[float], _param: float | None) -> float:
    return prod(weights)


def _agg_lukasiewicz(weights: list[float], _param: float | None) -> float:
    # Generalised n-ary Lukasiewicz: max(sum(w_i) - (n-1), 0)
    # Equivalent to repeated pairwise application.
    return max(sum(weights) - (len(weights) - 1), 0.0)


def _agg_einstein(weights: list[float], _param: float | None) -> float:
    return reduce(_einstein_pair, weights)


def _agg_geometric_mean(weights: list[float], _param: float | None) -> float:
    return prod(weights) ** (1.0 / len(weights))


def _agg_hamacher(weights: list[float], param: float | None) -> float:
    if param is None:
        raise ValueError(
            "HamacherProduct requires amt:logicParameter (gamma). "
            "None was supplied."
        )
    return reduce(lambda a, b: _hamacher_pair(a, b, param), weights)


# ──────────────────────────────────────────────────────────────────────────
# Registry — single source of truth
# ──────────────────────────────────────────────────────────────────────────
class LogicSpec(dict):
    """A row in the registry. Just a dict, but with a docstring for clarity.

    Keys:
        fn:            Callable[[list[float], float|None], float]
        arity:         "binary" | "n-ary"
        parametrised:  bool
    """


LOGIC_REGISTRY: dict[str, LogicSpec] = {
    GOEDEL:      LogicSpec(fn=_agg_goedel,         arity="binary", parametrised=False),
    PRODUCT:     LogicSpec(fn=_agg_product,        arity="binary", parametrised=False),
    LUKASIEWICZ: LogicSpec(fn=_agg_lukasiewicz,    arity="binary", parametrised=False),
    EINSTEIN:    LogicSpec(fn=_agg_einstein,       arity="binary", parametrised=False),
    GEOMETRIC:   LogicSpec(fn=_agg_geometric_mean, arity="n-ary",  parametrised=False),
    HAMACHER:    LogicSpec(fn=_agg_hamacher,       arity="binary", parametrised=True),
}


# ──────────────────────────────────────────────────────────────────────────
# Public API
# ──────────────────────────────────────────────────────────────────────────
def aggregate_weights(
    weights: list[float],
    logic_iri: str,
    parameter: float | None = None,
) -> float:
    """
    Aggregate a list of weights according to the given fuzzy logic operator.

    Parameters
    ----------
    weights
        Non-empty list of weights, each in [0, 1].
    logic_iri
        Full IRI of the AMT logic operator (e.g.
        ``"http://academic-meta-tool.xyz/vocab#GoedelLogic"``).
    parameter
        Optional numeric parameter, required for parametrised operators
        (Hamacher). Ignored for non-parametrised operators.

    Returns
    -------
    float
        Aggregated weight, clamped to [0, 1] and rounded to 6 decimals.

    Raises
    ------
    ValueError
        If ``weights`` is empty, the operator is unknown, or a parametrised
        operator is called without a parameter.
    """
    if not weights:
        raise ValueError("Cannot aggregate an empty weight list.")
    if logic_iri not in LOGIC_REGISTRY:
        raise ValueError(
            f"Unknown logic operator: {logic_iri!r}. "
            f"Known operators: {sorted(LOGIC_REGISTRY)}"
        )

    spec = LOGIC_REGISTRY[logic_iri]
    raw = spec["fn"](weights, parameter)

    # Clamp to [0, 1] and round for stability across floating-point edge cases.
    clamped = max(0.0, min(1.0, raw))
    return round(clamped, 6)


def get_arity(logic_iri: str) -> str:
    """Return ``"binary"`` or ``"n-ary"`` for a known logic operator."""
    return LOGIC_REGISTRY[logic_iri]["arity"]


def is_parametrised(logic_iri: str) -> bool:
    """Return True if the operator requires :param:`parameter` to be set."""
    return LOGIC_REGISTRY[logic_iri]["parametrised"]
