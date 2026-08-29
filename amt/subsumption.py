"""
AMT Subsumption
===============

Support for ``amt:SubsumptionAxiom`` — a statement about *roles*, not about
any particular pair of nodes::

    ex:SUB0001 a amt:SubsumptionAxiom ;
        amt:subRole   ex:ob ;
        amt:superRole ex:ol .

Read as: every ``ob`` edge is also an ``ol`` edge, at no lower weight.

Two semantics are implemented, and the caller picks one:

**Entailment** (the default of :func:`amt.reasoning.do_reasoning`)
    Given ``(x, ob, y, w)`` and ``ob ⊑ ol``, add ``(x, ol, y, w)``. The
    subsumption becomes explicit in the graph, which is what a downstream
    consumer that does not know the hierarchy needs. It increases the edge
    count.

**Redundancy elimination** (``minimal=True``)
    Given ``(x, ob, y, w₁)`` and ``(x, ol, y, w₂)`` with ``ob ⊑ ol`` and
    ``w₁ >= w₂``, suppress the ``ol`` edge: it says strictly less about the
    same pair at no greater confidence. When ``w₁ < w₂`` both are kept — a
    coarse relation derived along a strong path can be worth more than a
    fine relation derived along a weak one, and suppressing it would throw
    information away.

Elimination never removes an **asserted** edge. The reasoner is allowed to
drop conclusions it drew itself; it is not allowed to silently delete what
the user wrote down.

Why vocabularies need this
--------------------------

Vocabularies whose roles are sets of finer relations — Freksa's 29
semi-interval relations, for instance, where ``ob`` = {``<``, ``m``, ``o``}
and ``ol`` = {``<``, ``m``, ``o``, ``fi``, ``di``} — produce chains of
proper subset relations such as ``< ⊂ ob ⊂ ol ⊂ bd ⊂ ?``. Without
subsumption the reasoner derives every member of the chain independently.
All of them are true; all but the finest are redundant, and the coarsest
("no information about this pair") is actively misleading, because
something *is* known about the pair.
"""
from __future__ import annotations

from collections import defaultdict

__all__ = [
    "SUBSUMPTION_AXIOM_TYPE",
    "collect_direct_subsumptions",
    "transitive_superroles",
    "eliminate_redundant_edges",
]

SUBSUMPTION_AXIOM_TYPE = "SubsumptionAxiom"


# ─────────────────────────────────────────────────────────────────────────
# Reading the axioms
# ─────────────────────────────────────────────────────────────────────────
def collect_direct_subsumptions(axioms: list[dict]) -> list[tuple[str, str]]:
    """
    Return the declared ``(subRole, superRole)`` pairs, in the order the
    axioms appear, skipping malformed and reflexive ones.

    A reflexive axiom (``r ⊑ r``) is dropped rather than reported: it is
    vacuously true, it makes no difference to entailment, and keeping it
    would let a role suppress its own edge during elimination.
    """
    pairs: list[tuple[str, str]] = []
    seen: set[tuple[str, str]] = set()
    for axiom in axioms:
        if axiom.get("type") != SUBSUMPTION_AXIOM_TYPE:
            continue
        sub = axiom.get("subRole")
        sup = axiom.get("superRole")
        if not sub or not sup or sub == sup:
            continue
        if (sub, sup) in seen:
            continue
        seen.add((sub, sup))
        pairs.append((sub, sup))
    return pairs


def transitive_superroles(axioms: list[dict]) -> dict[str, set[str]]:
    """
    Return a mapping ``subRole -> {every super-role reachable from it}``.

    The transitive closure is computed here rather than assumed, so a file
    that declares only the covering relation (``< ⊑ ob``, ``ob ⊑ ol``)
    behaves exactly like one that spells out the full closure. Cycles are
    tolerated: a role never ends up as its own super-role, so two roles
    declared to subsume each other simply cannot suppress one another.
    """
    direct: dict[str, set[str]] = defaultdict(set)
    for sub, sup in collect_direct_subsumptions(axioms):
        direct[sub].add(sup)

    closure: dict[str, set[str]] = {}
    for role in direct:
        reached: set[str] = set()
        stack = list(direct[role])
        while stack:
            nxt = stack.pop()
            if nxt in reached:
                continue
            reached.add(nxt)
            stack.extend(direct.get(nxt, ()))
        reached.discard(role)  # no role subsumes itself
        if reached:
            closure[role] = reached
    return closure


# ─────────────────────────────────────────────────────────────────────────
# Redundancy elimination
# ─────────────────────────────────────────────────────────────────────────
def eliminate_redundant_edges(
    edges: list[dict],
    axioms: list[dict],
) -> tuple[list[dict], list[dict]]:
    """
    Drop inferred edges that are subsumed by a finer edge between the same
    pair of nodes at no lower weight.

    Parameters
    ----------
    edges
        A reasoned edge list, e.g. the output of
        :func:`amt.reasoning.do_reasoning`.
    axioms
        The axiom list; only ``SubsumptionAxiom`` entries are read.

    Returns
    -------
    (kept, removed)
        Two lists whose union is ``edges`` and whose intersection is empty.
        ``kept`` preserves the input order. Edge dicts are not copied — the
        objects in ``kept`` are the objects that were passed in.

    Notes
    -----
    Suppression requires ``weight(finer) >= weight(coarser)``. An asserted
    edge is never suppressed. A finer edge that is itself suppressed cannot
    justify suppressing anything else, so a chain ``< ⊂ ob ⊂ ol`` leaves
    exactly the finest surviving edge in place.
    """
    closure = transitive_superroles(axioms)
    if not closure:
        return (list(edges), [])

    # Group edges by node pair; within a pair, by role.
    by_pair: dict[tuple[str, str], dict[str, dict]] = defaultdict(dict)
    for e in edges:
        by_pair[(e["from"], e["to"])][e["role"]] = e

    doomed: set[int] = set()  # id() of the edge dicts to drop
    for roles in by_pair.values():
        if len(roles) < 2:
            continue
        for fine_role, fine_edge in roles.items():
            if id(fine_edge) in doomed:
                continue  # a suppressed edge justifies nothing
            for coarse_role in closure.get(fine_role, ()):
                coarse_edge = roles.get(coarse_role)
                if coarse_edge is None:
                    continue
                if not coarse_edge.get("inferred", False):
                    continue  # never delete asserted data
                if fine_edge["weight"] >= coarse_edge["weight"]:
                    doomed.add(id(coarse_edge))

    if not doomed:
        return (list(edges), [])

    kept = [e for e in edges if id(e) not in doomed]
    removed = [e for e in edges if id(e) in doomed]
    return (kept, removed)
