"""
AMT Visualisation
=================

Python port of ``amt-render.js`` using ``pyvis`` (which wraps vis.js).

Two entry points:

* :func:`build_network` – returns a configured :class:`pyvis.network.Network`
* :func:`render_to_html` – writes a self-contained HTML file
"""
from __future__ import annotations

import re
from pathlib import Path

from pyvis.network import Network

from .core import local_name
from .fw import effective_type
from .reasoning import do_reasoning

# Same colour order as ``AMT_PALETTE`` in ``amt-render.js``
_PALETTE = [
    {"bg": "coral", "border": "#c05a00", "font": "#000"},
    {"bg": "#5b9bd5", "border": "#2e75b6", "font": "#fff"},
    {"bg": "#70ad47", "border": "#538135", "font": "#fff"},
    {"bg": "#ffc000", "border": "#c07a00", "font": "#000"},
    {"bg": "#7030a0", "border": "#4b1a6e", "font": "#fff"},
    {"bg": "#ed7d31", "border": "#843c00", "font": "#fff"},
]


def build_network(
    nodes: dict,
    edges: list,
    concepts: dict,
    *,
    reasoning: bool = False,
    axioms: list | None = None,
    height: str = "600px",
    notebook: bool = False,
    reasoned_edges: list | None = None,
    cdn_resources: str = "in_line",
) -> Network:
    """
    Build a configured :class:`pyvis.network.Network` for an AMT graph.

    Parameters
    ----------
    nodes, edges, concepts
        Output of :func:`amt.core.load_amt`.
    reasoning
        If ``True``, run :func:`amt.core.do_reasoning` first; inferred edges
        are drawn as red dashed arrows.
    axioms
        Required when ``reasoning=True``.
    height
        CSS height for the canvas, e.g. ``"600px"``.
    notebook
        Pass ``True`` only when calling from inside a Jupyter notebook *and*
        you want pyvis to use its inline-iframe mode.
    cdn_resources
        pyvis option: ``"in_line"`` (default) embeds the library in the HTML,
        ``"remote"`` loads it from a CDN, ``"local"`` writes a ``lib/`` folder.
    reasoned_edges
        An already-reasoned edge list. Pass it to draw a graph produced
        with non-default reasoning options (e.g. ``minimal=True``) instead
        of reasoning again here. Ignored unless ``reasoning`` is set.
    """
    if not reasoning:
        display_edges = edges
    elif reasoned_edges is not None:
        display_edges = reasoned_edges
    else:
        display_edges = do_reasoning(edges, axioms or [])

    net = Network(
        height=height,
        width="100%",
        directed=True,
        notebook=notebook,
        bgcolor="#ffffff",
        font_color="#333333",
        cdn_resources=cdn_resources,
    )
    net.barnes_hut(
        gravity=-8000,
        spring_length=350,
        spring_strength=0.02,
        damping=0.5,
    )

    # Concept → colour
    color_map = {
        c: _PALETTE[i % len(_PALETTE)]
        for i, c in enumerate(concepts.keys())
    }

    for node in nodes.values():
        col = color_map.get(node["concept"], _PALETTE[0])
        concept_label = concepts.get(node["concept"], {}).get("label", "?")
        net.add_node(
            node["id"],
            label=node["label"],
            color={
                "background": col["bg"],
                "border": col["border"],
                "highlight": {
                    "background": "white",
                    "border": col["border"],
                },
            },
            shape="dot",
            size=20,
            font={"size": 16, "face": "monospace", "color": "#000"},
            title=f"Concept: {concept_label}",
        )

    # An edge may end at an IRI that was never declared as an instance of a
    # Concept (see amt.diagnostics, AMT-E101). pyvis refuses an edge to an unknown
    # node with a bare AssertionError, so such ends are drawn as grey
    # placeholders instead; the runner reports them in plain words.
    known = {n["id"] for n in nodes.values()}
    for e in display_edges:
        for end in (e["from"], e["to"]):
            if end not in known:
                known.add(end)
                net.add_node(
                    end,
                    label=local_name(end),
                    color={"background": "#e5e7eb", "border": "#9ca3af",
                           "highlight": {"background": "white", "border": "#9ca3af"}},
                    shape="dot",
                    size=14,
                    font={"size": 14, "face": "monospace", "color": "#555"},
                    title="Not declared: add amt:instanceOf for this IRI",
                )

    for e in display_edges:
        inferred = e.get("inferred", False)
        role_short = local_name(e["role"])
        w = round(e["weight"], 3)
        net.add_edge(
            e["from"],
            e["to"],
            label=f"{role_short}: {w}",
            width=max(1, w * 5),
            color={
                "color": "#cc0000" if inferred else "#333333",
                "highlight": "#555555",
            },
            arrows="to",
            dashes=inferred,
            font={
                "size": 11,
                "face": "monospace",
                "color": "#cc0000" if inferred else "#333333",
                "align": "middle",
            },
            title=_edge_tooltip(e),
        )

    return net


def _edge_tooltip(e: dict) -> str:
    """Hover text of an edge: asserted or inferred, then type and, if there is one, method."""
    parts = ["inferred" if e.get("inferred") else "asserted", f"type: {local_name(effective_type(e))}"]
    if e.get("method"):
        parts.append(f"method: {local_name(e['method'])}")
    return " | ".join(parts)


def render_to_html(
    nodes: dict,
    edges: list,
    concepts: dict,
    output_path: str | Path,
    *,
    reasoning: bool = False,
    axioms: list | None = None,
    height: str = "600px",
    reasoned_edges: list | None = None,
    cdn_resources: str = "in_line",
) -> Path:
    """
    Build the network and write a self-contained HTML file.
    Returns the path that was written.

    ``cdn_resources`` is handed to pyvis: ``"in_line"`` (the default) embeds the
    visualisation library, so the file works offline and loads nothing from a
    third party; ``"remote"`` writes a much smaller file that fetches the
    library from a CDN when it is opened.
    """
    net = build_network(
        nodes,
        edges,
        concepts,
        reasoning=reasoning,
        axioms=axioms,
        height=height,
        notebook=False,
        reasoned_edges=reasoned_edges,
        cdn_resources=cdn_resources,
    )
    out = Path(output_path)
    if cdn_resources == "local":
        net.save_graph(str(out))             # pyvis also copies its lib/ folder next to the file
        return out
    # pyvis opens the file with the platform's default encoding (cp1252 on Windows),
    # which cannot hold the embedded library: render the page ourselves, as UTF-8.
    html = net.generate_html().replace("\r\n", "\n")
    if cdn_resources != "remote":
        html = _drop_bootstrap(html)
    out.write_text(html, encoding="utf-8", newline="\n")
    return out


def _drop_bootstrap(html: str) -> str:
    """pyvis 0.3 always links Bootstrap from a CDN, though only its filter and select menus need it.

    AMT draws neither, so the two tags are removed: the file then loads nothing from a third party.
    """
    html = re.sub(r"\s*<link\s+href=\"https://cdn\.jsdelivr\.net/npm/bootstrap[^>]*?/>", "", html, flags=re.S)
    return re.sub(r"\s*<script\s+src=\"https://cdn\.jsdelivr\.net/npm/bootstrap[^>]*?></script>", "", html, flags=re.S)


# ─────────────────────────────────────────────────────────────────────────────
# Notebook helper – kept here so the CLI/library don't drag IPython in.
# Imported lazily so a missing ``IPython`` install doesn't break the package.
# ─────────────────────────────────────────────────────────────────────────────
def show_in_notebook(
    nodes: dict,
    edges: list,
    concepts: dict,
    *,
    reasoning: bool = False,
    axioms: list | None = None,
    height: str = "600px",
    filename: str = "_amt_graph.html",
) -> None:
    """
    Render the graph and embed it inline (works in classic Notebook,
    JupyterLab and VS Code). Requires ``IPython``.
    """
    from IPython.display import HTML, display  # local import on purpose

    out = render_to_html(
        nodes,
        edges,
        concepts,
        filename,
        reasoning=reasoning,
        axioms=axioms,
        height=height,
    )
    html_content = out.read_text(encoding="utf-8")
    html_escaped = html_content.replace("&", "&amp;").replace('"', "&quot;")
    h = int(height.replace("px", "")) + 20
    display(
        HTML(
            f'<iframe srcdoc="{html_escaped}" '
            f'width="100%" height="{h}px" '
            f'style="border:1px solid #ddd; border-radius:4px;"></iframe>'
        )
    )
