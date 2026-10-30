"""
AMT Reasoning Engine
====================

Forward-chaining reasoner over an AMT graph. Two public functions:

* :func:`do_reasoning` — apply RoleChain, Inverse and Subsumption axioms
  iteratively until no new edges are produced (fixed-point semantics).
* :func:`check_consistency` — verify Disjoint and SelfDisjoint integrity
  constraints against the reasoned edge set.

Inferred edges carry ``inferred=True`` and a ``provenance`` list of axiom
IRIs that contributed to their derivation. When an edge is derived through
multiple paths, the provenance lists are merged and the **maximum** weight
across paths is kept (standard semantics for fuzzy forward-chaining: any
path of evidence at strength w means the consequent holds at >= w).

Type and method (hextuple)
--------------------------

Every derived edge also says *how* and *what kind of*. A ``RoleChainAxiom``
sets the method to its logic (for example ``amt:GoedelLogic``) and the type to
the common type of its antecedent edges, or ``fw:FuzzinessWobbliness`` if they
differ (:func:`amt.fw.combine_types`). ``InverseAxiom`` and
``SubsumptionAxiom`` set no method and take the type of the source edge. The
default type (vagueness) is stored as ``None``.

If an edge is derived on several paths, the path with the highest weight
decides type and method; on equal weights the smallest method IRI wins (an
edge without method sorts first), then the smallest type IRI. Asserted edges
keep what they were given.

The input ``edges`` list is never mutated — :func:`do_reasoning` returns a
new list.

Subsumption
-----------

``amt:SubsumptionAxiom`` declares that one role is finer than another
(``ob ⊑ ol``). It has two possible readings, and ``minimal`` picks one:

``minimal=False`` (default)
    Entailment. Every ``ob`` edge also produces an ``ol`` edge at the same
    weight, so the hierarchy is spelled out in the exported graph for the
    benefit of consumers that do not know it.

``minimal=True``
    Redundancy elimination. Subsumption entailment is *not* applied, and
    after the fixed point every inferred edge that a finer edge between the
    same pair already implies at no lower weight is dropped. See
    :mod:`amt.subsumption`.

Files without ``SubsumptionAxiom`` behave identically under both settings.

Performance
-----------

Edges are held in a live index keyed by ``(role, from, to)`` and by
``(role, from)``, maintained incrementally as edges are added. Lookups
during chain application are therefore O(1) rather than a scan of the edge
list, and no index is rebuilt per axiom application. This matters for
vocabularies with hundreds of role-chain axioms — a composition table over
29 roles has 841 of them.
"""
from __future__ import annotations

import copy
from collections import defaultdict
from typing import Iterator

from .fw import combine_types, effective_type, stored_type
from .logic import aggregate_weights
from .subsumption import eliminate_redundant_edges


# ─────────────────────────────────────────────────────────────────────────
# Internal: live edge index
# ─────────────────────────────────────────────────────────────────────────
class _EdgeIndex:
    """
    Two views on the same edge dicts, kept in step with the result list.

    ``by_key``       maps ``(role, from, to)`` to the edge — used to decide
                     whether an inference produces a new edge or strengthens
                     an existing one.
    ``by_role_from`` maps ``role`` to ``from`` to the list of edges — used
                     to walk role chains.

    Edge dicts are shared by reference, so raising a weight in place needs
    no index update. Only appends do.
    """

    __slots__ = ("by_key", "by_role_from")

    def __init__(self, edges: list[dict]):
        self.by_key: dict[tuple[str, str, str], dict] = {}
        self.by_role_from: dict[str, dict[str, list[dict]]] = defaultdict(
            lambda: defaultdict(list)
        )
        for e in edges:
            self._register(e)

    def _register(self, e: dict) -> None:
        self.by_key[(e["role"], e["from"], e["to"])] = e
        self.by_role_from[e["role"]][e["from"]].append(e)

    def get(self, role: str, frm: str, to: str) -> dict | None:
        return self.by_key.get((role, frm, to))

    def outgoing(self, role: str, frm: str) -> list[dict]:
        starts = self.by_role_from.get(role)
        if not starts:
            return []
        return starts.get(frm, [])

    def starts(self, role: str) -> list[tuple[str, list[dict]]]:
        """Snapshot of ``(from_node, edges)`` pairs for one role."""
        starts = self.by_role_from.get(role)
        if not starts:
            return []
        return list(starts.items())

    def append(self, result: list[dict], edge: dict) -> None:
        result.append(edge)
        self._register(edge)


# ─────────────────────────────────────────────────────────────────────────
# Public API
# ─────────────────────────────────────────────────────────────────────────
def do_reasoning(
    edges: list[dict],
    axioms: list[dict],
    *,
    max_iterations: int = 100,
    minimal: bool = False,
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
    minimal
        If True, skip subsumption entailment and instead suppress inferred
        edges that a finer edge between the same pair already implies at no
        lower weight. Has no effect on files without ``SubsumptionAxiom``.

    Returns
    -------
    list[dict]
        New list containing all asserted edges plus all inferred edges.
        Inferred edges have ``inferred=True`` and a ``provenance`` list.

    See also
    --------
    reason_with_stats
        Same computation, but also reports how many iterations the fixed
        point took and how many edges minimal mode suppressed.
    """
    result, _stats = reason_with_stats(
        edges, axioms, max_iterations=max_iterations, minimal=minimal
    )
    return result


def reason_with_stats(
    edges: list[dict],
    axioms: list[dict],
    *,
    max_iterations: int = 100,
    minimal: bool = False,
) -> tuple[list[dict], dict]:
    """
    :func:`do_reasoning` plus a small statistics dict.

    Returns
    -------
    (result, stats)
        ``stats`` has the keys ``iterations`` (how many passes over the
        axiom list were needed, including the final one that changed
        nothing), ``suppressed`` (edges dropped by minimal mode) and
        ``reached_fixpoint`` (False if ``max_iterations`` ran out, which
        means the result is incomplete).
    """
    result = copy.deepcopy(edges)
    # Make sure even asserted edges have the new fields, even if they
    # came from an older loader.
    for e in result:
        e.setdefault("inferred",   False)
        e.setdefault("provenance", [])
        e.setdefault("type",       None)
        e.setdefault("method",     None)
        e.setdefault("evidence",   None)

    index = _EdgeIndex(result)

    iterations = 0
    reached_fixpoint = False
    for _ in range(max_iterations):
        iterations += 1
        changed = False
        for axiom in axioms:
            atype = axiom.get("type")
            if atype == "RoleChainAxiom":
                changed |= _apply_role_chain(result, axiom, index)
            elif atype == "InverseAxiom":
                changed |= _apply_inverse(result, axiom, index)
            elif atype == "SubsumptionAxiom" and not minimal:
                changed |= _apply_subsumption(result, axiom, index)
        if not changed:
            reached_fixpoint = True
            break

    suppressed = 0
    if minimal:
        result, removed = eliminate_redundant_edges(result, axioms)
        suppressed = len(removed)

    stats = {
        "iterations":       iterations,
        "suppressed":       suppressed,
        "reached_fixpoint": reached_fixpoint,
    }
    return (result, stats)


def check_consistency(
    edges: list[dict],
    axioms: list[dict],
    *,
    reasoned: list[dict] | None = None,
) -> tuple[bool, list[str]]:
    """
    Check ``DisjointAxiom`` and ``SelfDisjointAxiom`` integrity constraints
    against the reasoned edge set.

    Parameters
    ----------
    edges, axioms
        As for :func:`do_reasoning`.
    reasoned
        An already-reasoned edge list. Pass it to avoid running the fixed
        point twice; without it the function reasons internally with the
        default settings.

        Passing a ``minimal=True`` edge list is legitimate — it checks the
        graph the caller is actually going to export — but note that a
        ``DisjointAxiom`` stated over a coarse role will not fire on an
        edge that redundancy elimination suppressed.

    Returns
    -------
    (is_consistent, violations)
        ``violations`` is a list of human-readable strings; empty when
        ``is_consistent`` is ``True``.
    """
    if reasoned is None:
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
def _apply_role_chain(result: list[dict], axiom: dict, index: _EdgeIndex) -> bool:
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

    # Materialise the matches before adding anything. The index is live,
    # so consuming the generator while appending would mutate the very
    # lists being walked and let an axiom feed on its own output within a
    # single application. The fixed-point loop handles the rest.
    matches = list(_find_chain_matches(index, antecedents))

    changed = False
    for match in matches:
        weight = aggregate_weights(match["weights"], logic, parameter)
        if weight <= 0:
            continue
        changed |= _add_or_strengthen_edge(
            result,
            index,
            role=consequent,
            frm=match["start"],
            to=match["end"],
            weight=weight,
            provenance_axiom=axiom_iri,
            type_=stored_type(combine_types(e.get("type") for e in match["edges"])),
            method=logic,
        )
    return changed


def _find_chain_matches(
    index: _EdgeIndex,
    antecedent_roles: list[str],
) -> Iterator[dict]:
    """
    Yield every node sequence (n0, n1, ..., nk) where there is an edge
    n_i --antecedent_roles[i]--> n_{i+1}.

    Each yielded match is a dict with::

        {"start": IRI, "end": IRI, "weights": [w1, w2, ..., wk],
         "edges": [e1, e2, ..., ek]}
    """
    if not antecedent_roles:
        return

    first_role = antecedent_roles[0]
    rest_roles = antecedent_roles[1:]

    # Seed the walk with every edge matching the first role
    for from_node, first_edges in index.starts(first_role):
        for first_edge in list(first_edges):
            yield from _extend_chain(
                start=from_node,
                current=first_edge["to"],
                remaining_roles=rest_roles,
                weights_so_far=[first_edge["weight"]],
                edges_so_far=[first_edge],
                index=index,
            )


def _extend_chain(
    start: str,
    current: str,
    remaining_roles: list[str],
    weights_so_far: list[float],
    edges_so_far: list[dict],
    index: _EdgeIndex,
) -> Iterator[dict]:
    """Recursive helper for :func:`_find_chain_matches`."""
    if not remaining_roles:
        yield {"start": start, "end": current, "weights": weights_so_far, "edges": edges_so_far}
        return

    next_role = remaining_roles[0]
    further = remaining_roles[1:]

    for next_edge in list(index.outgoing(next_role, current)):
        yield from _extend_chain(
            start=start,
            current=next_edge["to"],
            remaining_roles=further,
            weights_so_far=weights_so_far + [next_edge["weight"]],
            edges_so_far=edges_so_far + [next_edge],
            index=index,
        )


def _add_or_strengthen_edge(
    result: list[dict],
    index: _EdgeIndex,
    *,
    role: str,
    frm: str,
    to: str,
    weight: float,
    provenance_axiom: str,
    type_: str | None = None,
    method: str | None = None,
) -> bool:
    """
    Add a new inferred edge, or strengthen an existing one.

    Semantics:
      - If no edge (role, frm, to) exists: append a new inferred edge.
      - If an asserted edge exists: do not override its weight, but do
        merge the axiom IRI into its provenance (a record that this axiom
        also independently supports the assertion).
      - If an inferred edge exists with lower weight: raise the weight,
        take type and method of the new path, keep merged provenance.
      - If an inferred edge exists with equal weight: keep the path whose
        (method, type) is smaller, so the result does not depend on the
        order in which paths are found.
      - If an inferred edge exists with higher weight: just merge
        provenance.

    ``type_`` is the stored form (``None`` = default), see :mod:`amt.fw`.
    """
    existing = index.get(role, frm, to)
    if existing is None:
        index.append(result, {
            "role":       role,
            "from":       frm,
            "to":         to,
            "weight":     weight,
            "inferred":   True,
            "provenance": [provenance_axiom] if provenance_axiom else [],
            "type":       type_,
            "method":     method,
            "evidence":   None,
        })
        return True

    # Edge already there: track provenance regardless
    changed = False
    if provenance_axiom and provenance_axiom not in existing["provenance"]:
        existing["provenance"].append(provenance_axiom)
        changed = True

    # Only strengthen weights of inferred edges; never overwrite asserted ones.
    if existing.get("inferred", False):
        if existing["weight"] < weight:
            existing["weight"] = weight
            existing["type"] = type_
            existing["method"] = method
            changed = True
        elif existing["weight"] == weight:
            new_key = (method or "", effective_type({"type": type_}))
            old_key = (existing.get("method") or "", effective_type(existing))
            if new_key < old_key:
                # A different type can change what depends on this edge; a
                # different method cannot, so only the former is a change.
                changed |= effective_type({"type": type_}) != effective_type(existing)
                existing["type"] = type_
                existing["method"] = method

    return changed


# ─────────────────────────────────────────────────────────────────────────
# Internal: InverseAxiom application
# ─────────────────────────────────────────────────────────────────────────
def _apply_inverse(result: list[dict], axiom: dict, index: _EdgeIndex) -> bool:
    ant = axiom.get("antecedent")
    inv = axiom.get("inverse")
    axiom_iri = axiom.get("iri", "")
    if not ant or not inv:
        return False

    changed = False
    # Snapshot so we don't iterate over edges we just added
    for _from_node, out_edges in index.starts(ant):
        for e in list(out_edges):
            changed |= _add_or_strengthen_edge(
                result,
                index,
                role=inv,
                frm=e["to"],
                to=e["from"],
                weight=e["weight"],
                provenance_axiom=axiom_iri,
                type_=stored_type(e.get("type")),
            )
    return changed


# ─────────────────────────────────────────────────────────────────────────
# Internal: SubsumptionAxiom application (entailment reading)
# ─────────────────────────────────────────────────────────────────────────
def _apply_subsumption(result: list[dict], axiom: dict, index: _EdgeIndex) -> bool:
    """
    Every ``subRole`` edge is also a ``superRole`` edge at the same weight.

    Only the directly declared pair is applied here; the fixed-point loop
    walks the chain ``< ⊑ ob ⊑ ol ⊑ ?`` one link per iteration, so a file
    that declares only the covering relation gets the same closure as one
    that spells every pair out.
    """
    sub = axiom.get("subRole")
    sup = axiom.get("superRole")
    axiom_iri = axiom.get("iri", "")
    if not sub or not sup or sub == sup:
        return False

    changed = False
    for _from_node, out_edges in index.starts(sub):
        for e in list(out_edges):
            changed |= _add_or_strengthen_edge(
                result,
                index,
                role=sup,
                frm=e["from"],
                to=e["to"],
                weight=e["weight"],
                provenance_axiom=axiom_iri,
                type_=stored_type(e.get("type")),
            )
    return changed
