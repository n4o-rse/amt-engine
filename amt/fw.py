"""
FW vocabulary — type and method of a statement
==============================================

The AMT statement is a reified quadruple (subject, role, object, weight). The
FW ontology (``caa-datadragons/FW_Ontology``, namespace
``http://w3id.org/fw_ontology/``, prefix ``fw:``) adds two things a statement
can say about itself, which together make it a hextuple:

``fw:hasType``
    what kind of fuzziness the weight expresses — one of the three individuals
    :data:`VAGUENESS`, :data:`UNCERTAINTY`, :data:`FUZZINESS_WOBBLINESS`.
``fw:hasMethod``
    how the weight was obtained, for example an AMT logic such as
    ``amt:GoedelLogic`` for a weight the reasoner computed.

Both are optional. In AMT, **a statement without a type is a vagueness
statement** (:data:`DEFAULT_TYPE`); the edge dict then carries ``type: None``
and :func:`effective_type` returns :data:`VAGUENESS`.

Edge dict keys added by the hextuple (all default to ``None``)::

    "type":     str | None,   # IRI of the fw:FW_Type individual, None = default
    "method":   str | None,   # IRI of the method individual
    "evidence": list | None,  # passed through unchanged, see amt.core

The module has no dependency on the rest of the package, so ``amt.core``,
``amt.reasoning`` and the exporters can all import it.
"""
from __future__ import annotations

from typing import Iterable

from rdflib import Namespace

FW = Namespace("http://w3id.org/fw_ontology/")
FW_PFX = str(FW)

VAGUENESS = FW_PFX + "Vagueness"
UNCERTAINTY = FW_PFX + "Uncertainty"
FUZZINESS_WOBBLINESS = FW_PFX + "FuzzinessWobbliness"

#: The three individuals of ``fw:FW_Type`` that AMT knows, in a fixed order.
KNOWN_TYPES: tuple[str, ...] = (FUZZINESS_WOBBLINESS, UNCERTAINTY, VAGUENESS)

#: What a statement is when nothing else is said.
DEFAULT_TYPE = VAGUENESS


def effective_type(edge: dict) -> str:
    """The type that counts for an edge: its own, or :data:`DEFAULT_TYPE`."""
    return edge.get("type") or DEFAULT_TYPE


def stored_type(type_iri: str | None) -> str | None:
    """The value to put in an edge dict: ``None`` for the default type."""
    if not type_iri or type_iri == DEFAULT_TYPE:
        return None
    return type_iri


def combine_types(types: Iterable[str | None]) -> str:
    """
    The effective type of a statement derived from several others.

    If all antecedents have the same effective type, the result has it too.
    If they differ, the result is :data:`FUZZINESS_WOBBLINESS`, the common
    broader concept of ``fw:Vagueness`` and ``fw:Uncertainty``. A missing type
    counts as :data:`VAGUENESS`. Without any antecedent the result is the
    default.
    """
    seen = {t or DEFAULT_TYPE for t in types}
    if not seen:
        return DEFAULT_TYPE
    if len(seen) == 1:
        return next(iter(seen))
    return FUZZINESS_WOBBLINESS
