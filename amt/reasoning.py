"""
AMT Reasoning Engine
====================

Forward-chaining reasoner over an AMT graph. Two public functions:

* :func:`do_reasoning` — apply RoleChain and Inverse axioms iteratively
  until no new edges are produced (fixed-point semantics).
* :func:`check_consistency` — verify Disjoint and SelfDisjoint integrity
  constraints against the reasoned edge set.

Inferred edges carry ``inferred=True`` and a ``provenance`` list of axiom
IRIs that contributed to their derivation. When an edge is derived through
multiple paths, the provenance lists are merged and the **maximum** weight
across paths is kept (standard semantics for fuzzy forward-chaining: any
path of evidence at strength w means the consequent holds at >= w).

The input ``edges`` list is never mutated — :func:`do_reasoning` returns a
new list.
"""
from __future__ import annotations

import copy
from collections import defaultdict
from typing import Iterator

from .logic import aggregate_weights


# ─────────────────────────────────────────────────────────────────────────
# Public API
# ─────────────────────────────────────────────────────────────────────────
def do_reasoning(
    edges: list[dict],
    axioms: list[dict],
    *,
    max_iterations: int = 100,
) -> list[dict]:
    """
    Apply InferenceAxiom rules iteratively to a fixed point.

    Parameters
    ----------
    edges
        List of edge dicts (asserted only, typically from
        :func:`amt.core.load_amt`).
    axioms
        List of axiom dicts as produced by the loader.
    max_iterations
        Safety bound to prevent infinite loops in case of a bug. The fixed
        point is normally reached within len(axioms)+1 iterations on real
        data; 100 is a generous upper bound.

    Returns
    -------
    list[dict]
        New list containing all asserted edges plus all inferred edges.
        Inferred edges have ``inferred=True`` and a ``provenance`` list.
    """
    result = copy.deepcopy(edges)
    # Make sure even asserted edges have the new fields, even if they
    # came from an older loader.
    for e in result:
        e.setdefault("inferred",   False)
        e.setdefault("provenance", [])

    for _ in range(max_iterations):
        changed = False
        for axiom in axioms:
            if axiom["type"] == "RoleChainAxiom":
                changed |= _apply_role_chain(result, axiom)
            elif axiom["type"] == "InverseAxiom":
                changed |= _apply_inverse(result, axiom)
        if not changed:
            break

    return result


def check_consistency(
    edges: list[dict],
    axioms: list[dict],
) -> tuple[bool, list[str]]:
    """
    Check ``DisjointAxiom`` and ``SelfDisjointAxiom`` integrity constraints
    against the reasoned edge set.

    Returns
    -------
    (is_consistent, violations)
        ``violations`` is a list of human-readable strings; empty when
        ``is_consistent`` is ``True``.
    """
    reasoned = do_reasoning(edges, axioms)
    violations: list[str] = []

    by_endpoint: dict[tuple[str, str, str], dict] = {
        (e["role"], e["from"], e["to"]): e for e in reasoned
    }

    def _has(role, frm, to):
        return (role, frm, to) in by_endpoint

    def _short(iri: str) -> str:
        return iri.split("/")[-1].split("#")[-1]

    for axiom in axioms:
        if axiom["type"] == "DisjointAxiom":
            r1 = axiom.get("role1")
            r2 = axiom.get("role2")
            for e in reasoned:
                if e["role"] == r1 and _has(r2, e["from"], e["to"]):
                    violations.append(
                        f"DisjointAxiom violated: {_short(e['from'])} "
                        f"has both {_short(r1)} and {_short(r2)} "
                        f"to {_short(e['to'])}"
                    )
        elif axiom["type"] == "SelfDisjointAxiom":
            role = axiom.get("role")
            for e in reasoned:
                if e["role"] == role and e["from"] == e["to"]:
                    violations.append(
                        f"SelfDisjointAxiom violated: "
                        f"{_short(e['from'])} has self-loop via {_short(role)}"
                    )

    return (len(violations) == 0, violations)


# ─────────────────────────────────────────────────────────────────────────
# Internal: RoleChainAxiom application
# ─────────────────────────────────────────────────────────────────────────
def _apply_role_chain(result: list[dict], axiom: dict) -> bool:
    """
    Find every length-n chain that matches ``antecedents`` and create or
    update the consequent edge. Returns True if any change was made.
    """
    antecedents: list[str] = axiom.get("antecedents", [])
    consequent: str = axiom.get("consequent", "")
    logic: str = axiom.get("logic", "")
    parameter = axiom.get("logicParameter")
    axiom_iri: str = axiom.get("iri", "")

    if not antecedents or not consequent or not logic:
        return False

    changed = False
    for match in _find_chain_matches(result, antecedents):
        weight = aggregate_weights(match["weights"], logic, parameter)
        if weight <= 0:
            continue
        changed |= _add_or_strengthen_edge(
            result,
            role=consequent,
            frm=match["start"],
            to=match["end"],
            weight=weight,
            provenance_axiom=axiom_iri,
        )
    return changed


def _find_chain_matches(
    edges: list[dict],
    antecedent_roles: list[str],
) -> Iterator[dict]:
    """
    Yield every node sequence (n0, n1, ..., nk) where there is an edge
    n_i --antecedent_roles[i]--> n_{i+1}.

    Implementation: index edges by (role, from-node) for fast extension,
    then perform a depth-first walk along the chain.

    Each yielded match is a dict with::

        {"start": IRI, "end": IRI, "weights": [w1, w2, ..., wk]}
    """
    # Index: role -> from_iri -> list[edge]
    index: dict[str, dict[str, list[dict]]] = defaultdict(lambda: defaultdict(list))
    for e in edges:
        index[e["role"]][e["from"]].append(e)

    if not antecedent_roles:
        return

    first_role = antecedent_roles[0]
    rest_roles = antecedent_roles[1:]

    # Seed the walk with every edge matching the first role
    for from_node, first_edges in index[first_role].items():
        for first_edge in first_edges:
            yield from _extend_chain(
                start=from_node,
                current=first_edge["to"],
                remaining_roles=rest_roles,
                weights_so_far=[first_edge["weight"]],
                index=index,
            )


def _extend_chain(
    start: str,
    current: str,
    remaining_roles: list[str],
    weights_so_far: list[float],
    index: dict[str, dict[str, list[dict]]],
) -> Iterator[dict]:
    """Recursive helper for :func:`_find_chain_matches`."""
    if not remaining_roles:
        yield {"start": start, "end": current, "weights": weights_so_far}
        return

    next_role = remaining_roles[0]
    further = remaining_roles[1:]

    for next_edge in index[next_role].get(current, ()):
        yield from _extend_chain(
            start=start,
            current=next_edge["to"],
            remaining_roles=further,
            weights_so_far=weights_so_far + [next_edge["weight"]],
            index=index,
        )


def _add_or_strengthen_edge(
    result: list[dict],
    *,
    role: str,
    frm: str,
    to: str,
    weight: float,
    provenance_axiom: str,
) -> bool:
    """
    Add a new inferred edge, or strengthen an existing one.

    Semantics:
      - If no edge (role, frm, to) exists: append a new inferred edge.
      - If an asserted edge exists: do not override its weight, but do
        merge the axiom IRI into its provenance (a record that this axiom
        also independently supports the assertion).
      - If an inferred edge exists with lower weight: raise the weight,
        keep merged provenance.
      - If an inferred edge exists with equal-or-higher weight: just merge
        provenance.
    """
    existing = next(
        (
            e for e in result
            if e["role"] == role and e["from"] == frm and e["to"] == to
        ),
        None,
    )
    if existing is None:
        result.append({
            "role":       role,
            "from":       frm,
            "to":         to,
            "weight":     weight,
            "inferred":   True,
            "provenance": [provenance_axiom] if provenance_axiom else [],
        })
        return True

    # Edge already there: track provenance regardless
    changed = False
    if provenance_axiom and provenance_axiom not in existing["provenance"]:
        existing["provenance"].append(provenance_axiom)
        changed = True

    # Only strengthen weights of inferred edges; never overwrite asserted ones.
    if existing.get("inferred", False) and existing["weight"] < weight:
        existing["weight"] = weight
        changed = True

    return changed


# ─────────────────────────────────────────────────────────────────────────
# Internal: InverseAxiom application
# ─────────────────────────────────────────────────────────────────────────
def _apply_inverse(result: list[dict], axiom: dict) -> bool:
    ant = axiom.get("antecedent")
    inv = axiom.get("inverse")
    axiom_iri = axiom.get("iri", "")
    if not ant or not inv:
        return False

    changed = False
    # Snapshot the list so we don't iterate over edges we just added
    for e in list(result):
        if e["role"] == ant:
            changed |= _add_or_strengthen_edge(
                result,
                role=inv,
                frm=e["to"],
                to=e["from"],
                weight=e["weight"],
                provenance_axiom=axiom_iri,
            )
    return changed
