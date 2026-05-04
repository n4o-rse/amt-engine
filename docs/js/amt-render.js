// ============================================================
// AMT - Academic Meta Tool
// amt-render.js - Graph rendering, node/edge styling, UI logic
// Depends on: amt.js, vis.js, jQuery, Materialize
// ============================================================

// ------------------------------------------------------------
// Global AMT state
// ------------------------------------------------------------
var _AMT = {};
_AMT.prefix    = "http://github.com/leiza-scit/CAA2026-amt/";
_AMT.graph     = {};
_AMT.edit      = false;
_AMT.thisNodes = [];
_AMT.thisEdges = [];
_AMT.inverse   = false;
_AMT.mode      = "potter";
_AMT.reasoning = false;
_AMT.rdf       = "";

// ------------------------------------------------------------
// Colour palette – one entry per Concept (auto-assigned)
// ------------------------------------------------------------
var AMT_PALETTE = [
    { bg: "coral",   border: "#c05a00", font: "#000" },
    { bg: "#5b9bd5", border: "#2e75b6", font: "#fff" },
    { bg: "#70ad47", border: "#538135", font: "#fff" },
    { bg: "#ffc000", border: "#c07a00", font: "#000" },
    { bg: "#7030a0", border: "#4b1a6e", font: "#fff" },
    { bg: "#ed7d31", border: "#843c00", font: "#fff" }
];

// ------------------------------------------------------------
// styleNodes: assign colour/shape per concept (auto-palette)
// ------------------------------------------------------------
var styleNodes = function(nodes) {
    // Build concept → palette index map in encounter order
    var conceptIndex = {};
    var counter = 0;
    for (var i in nodes) {
        var c = nodes[i].concept;
        if (c && !(c in conceptIndex)) {
            conceptIndex[c] = counter % AMT_PALETTE.length;
            counter++;
        }
    }
    for (var i in nodes) {
        if (!_AMT.edit) {
            nodes[i].chosen = false;
        }
        var cidx = conceptIndex[nodes[i].concept];
        var col  = AMT_PALETTE[cidx !== undefined ? cidx : 0];
        nodes[i].color = {
            background: col.bg,
            border:     col.border,
            highlight:  { background: "white", border: col.border }
        };
        nodes[i].shape = "dot";
        nodes[i].size  = 20;
        nodes[i].font  = { size: 16, face: "monospace", color: "#000" };
    }
    return nodes;
};

// ------------------------------------------------------------
// shortenURI: turn a full IRI into a CURIE using the prefix map
// captured from the TTL (set in amt.js after N3 parsing).
// Falls back to the part after # or the last / if no prefix matches.
// The "ex:" prefix is special-cased to render as bare local names
// (matches the AMT viewer convention for instance/role data).
// ------------------------------------------------------------
var shortenURI = function(uri) {
    if (typeof uri !== "string") return uri;
    var prefixes = (_AMT && _AMT.prefixes) ? _AMT.prefixes : {};

    // Find the longest matching namespace (so e.g. amt-vocab# wins over amt#)
    var bestPrefix = null;
    var bestNs     = "";
    for (var p in prefixes) {
        var ns = prefixes[p];
        if (ns && uri.indexOf(ns) === 0 && ns.length > bestNs.length) {
            bestPrefix = p;
            bestNs     = ns;
        }
    }
    if (bestPrefix !== null) {
        var local = uri.substring(bestNs.length);
        // Convention: drop the prefix label for the document's own "ex:"
        // namespace so role labels stay short (e.g. "closeMatch" not "ex:closeMatch")
        return bestPrefix === "ex" ? local : bestPrefix + ":" + local;
    }

    // Fallback: split on # or last /
    var hash = uri.lastIndexOf("#");
    if (hash >= 0) return uri.substring(hash + 1);
    var slash = uri.lastIndexOf("/");
    if (slash >= 0) return uri.substring(slash + 1);
    return uri;
};

// ------------------------------------------------------------
// styleEdges: uniform styling for all edges
//   black  = original assertion
//   red    = reasoned inference (set in amt.js updateReasoning)
// ------------------------------------------------------------
var styleEdges = function(edges) {
    for (var i in edges) {
        var isReasoned = edges[i].font && edges[i].font.color === "red";
        var roleShort  = shortenURI(edges[i].role);
        var weightVal  = Math.round(edges[i].width * 1000) / 1000;

        edges[i].arrowStrikethrough = false;
        edges[i].chosen  = false;
        edges[i].hidden  = (edges[i].width < 0.0000001);
        edges[i].arrows  = "to";
        edges[i].length  = 350;
        edges[i].smooth  = { type: "dynamic" };
        edges[i].label   = roleShort + ": " + weightVal;
        edges[i].color   = {
            color:     isReasoned ? "red" : "#000000",
            highlight: "#555555"
        };
        edges[i].font = {
            align: "middle",
            size:  11,
            color: isReasoned ? "red" : "#000000",
            face:  "monospace"
        };
    }
    return edges;
};

// ------------------------------------------------------------
// vis.js network options
// ------------------------------------------------------------
var AMT_VIS_OPTIONS = {
    layout: {
        randomSeed: 5
    },
    physics: {
        enabled: true,
        barnesHut: {
            gravitationalConstant: -8000,
            springLength:          350,
            springConstant:        0.02,
            damping:               0.5
        }
    },
    edges: {
        length: 350
    }
};

// ------------------------------------------------------------
// update: (re)load data and render the graph
// ------------------------------------------------------------
var update = function() {
    _AMT.amt = new AMT();
    _AMT.amt.load(function() {
        var graph = _AMT.amt.getGraph(false, true);
        _AMT.graph.nodes = new vis.DataSet(graph.nodes);
        _AMT.graph.edges = new vis.DataSet(graph.edges);
    });

    setTimeout(function() {
        new vis.Network(
            document.getElementById("graph"),
            { nodes: _AMT.graph.nodes, edges: _AMT.graph.edges },
            AMT_VIS_OPTIONS
        );

        var updated = _AMT.amt.getGraph(_AMT.reasoning, false);
        _AMT.graph.edges.clear();
        _AMT.graph.nodes.clear();

        updated.nodes = styleNodes(updated.nodes);
        updated.edges = styleEdges(updated.edges);

        _AMT.graph.nodes.update(updated.nodes);
        _AMT.graph.edges.update(updated.edges);
        _AMT.thisNodes = updated.nodes;
        _AMT.thisEdges = updated.edges;

        $("#title").html($("#amt-viz option:selected").text());
    }, 1000);
};

// ------------------------------------------------------------
// UI handlers
// ------------------------------------------------------------
var toggleReasoning = function() {
    if (_AMT.reasoning) {
        _AMT.reasoning = false;
        $("#r-but").removeClass("blue").addClass("red");
    } else {
        _AMT.reasoning = true;
        $("#r-but").removeClass("red").addClass("blue");
    }
    update();
};

var openGraphPropModal = function(close) {
    $("#amt-viz").material_select();
    if (close) $("#graphPropModal").modal("close");
    else       $("#graphPropModal").modal("open");
};

var openRdfModal = function(close) {
    if (close) $("#rdfModal").modal("close");
    else       $("#rdfModal").modal("open");
};

var reloadGraphWithProperties = function() {
    _AMT.mode = $("#amt-viz").val();
    update();
    $("#graphPropModal").modal("close");
};

// ------------------------------------------------------------
// exportRDF: serialise current graph state to Turtle and show
// ------------------------------------------------------------
var exportRDF = function() {
    var ex   = _AMT.prefix;
    var out  = "";
    out += "@prefix amt:  <http://academic-meta-tool.xyz/vocab#> .\r\n";
    out += "@prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .\r\n";
    out += "@prefix rdf:  <http://www.w3.org/1999/02/22-rdf-syntax-ns#> .\r\n";
    out += "@prefix ex:   <" + ex + "> .\r\n";
    out += "\r\n";
    for (var node in _AMT.thisNodes) {
        var n = _AMT.thisNodes[node];
        out += "ex:" + n.id.replace(ex, "")      + " amt:instanceOf ex:" + n.concept.replace(ex, "") + " .\r\n";
        out += "ex:" + n.id.replace(ex, "")      + " rdfs:label \""      + n.label                   + "\" .\r\n";
    }
    out += "\r\n";
    for (var edge in _AMT.thisEdges) {
        var e = _AMT.thisEdges[edge];
        var blank = "_:" + StrID();
        var w = (typeof e.width === "number") ? e.width : parseFloat(e.width) || 0;
        if (w > 1.0) w = 1.0;
        out += blank + " rdf:subject   ex:" + e.from.replace(ex, "")  + " .\r\n";
        out += blank + " rdf:predicate ex:" + e.role.replace(ex, "")  + " .\r\n";
        out += blank + " rdf:object    ex:" + e.to.replace(ex, "")    + " .\r\n";
        out += blank + " amt:weight    \"" + w + "\"^^<http://www.w3.org/2001/XMLSchema#double> .\r\n";
    }
    out = out.replace(/Infinity/g, "1.0");

    $("#hiddenclipboard").text(out);
    copyToClipboard("#hiddenclipboard");
    console.log(out);
    _AMT.rdf = out;
    $("#rdf").val(out);
    openRdfModal();
};

// ------------------------------------------------------------
// DOM ready
// ------------------------------------------------------------
$(function() {
    update();
    $("#rdfModal").modal({
        complete: function() { openRdfModal(true); }
    });
    $("#graphPropModal").modal({
        dismissible: false,
        complete: function() { openGraphPropModal(true); }
    });
});
