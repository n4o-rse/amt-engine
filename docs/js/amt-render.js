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
// Node colours: the AMT palette (design/palette.yaml): teal, gold, steel, bronze, emerald, mint.
var AMT_PALETTE = [
    { bg: "#4a9a82", border: "#184838", font: "#000" },
    { bg: "#e8b878", border: "#8a5a1a", font: "#000" },
    { bg: "#8fa3c4", border: "#2c3a52", font: "#000" },
    { bg: "#c8833f", border: "#8a5a1a", font: "#000" },
    { bg: "#1f6b57", border: "#184838", font: "#fff" },
    { bg: "#cfe6dc", border: "#1f6b57", font: "#000" }
];

// Edge colours come from the page's CSS variables (assets/palette.css), with the palette values as fallback.
var amtColour = function(name, fallback) {
    try {
        var v = getComputedStyle(document.documentElement).getPropertyValue("--" + name).trim();
        return v || fallback;
    } catch (e) { return fallback; }
};

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
//   steel  = original assertion
//   red    = reasoned inference (set in amt.js updateReasoning)
// ------------------------------------------------------------
var styleEdges = function(edges) {
    for (var i in edges) {
        var isReasoned = !!edges[i].inferred || (edges[i].font && edges[i].font.color === "red");
        var roleShort  = shortenURI(edges[i].role);
        var weightVal  = Math.round(edges[i].width * 1000) / 1000;

        edges[i].arrowStrikethrough = false;
        edges[i].chosen  = false;
        edges[i].hidden  = (edges[i].width < 0.0000001);
        edges[i].arrows  = "to";
        edges[i].length  = 350;
        edges[i].smooth  = { type: "dynamic" };
        edges[i].label   = roleShort + ": " + weightVal;
        // Hover text: asserted or inferred, the type (vagueness unless the
        // statement says otherwise) and, if there is one, the method.
        edges[i].title   = (isReasoned ? "inferred" : "asserted") +
            " | type: " + (edges[i].type ? shortenURI(edges[i].type) : "Vagueness") +
            (edges[i].method ? " | method: " + shortenURI(edges[i].method) : "");
        edges[i].color   = {
            color:     isReasoned ? amtColour("inferred", "#c62828") : amtColour("asserted", "#2c3a52"),
            highlight: "#555555"
        };
        edges[i].font = {
            align: "middle",
            size:  11,
            color: isReasoned ? amtColour("inferred", "#c62828") : amtColour("asserted", "#2c3a52"),
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
var _network = null;

var showStatus = function(amt) {
    var err = amt.getError();
    var el  = $("#status");
    if (err) {
        el.text("Could not load the data: " + err).css("color", "#ffb3b3").attr("title", "");
        return;
    }
    var v = amt.getViolations();
    if (v.length === 0) {
        el.text("consistent").css("color", "#b9f6ca").attr("title", "");
    } else {
        el.text(v.length + " consistency violation" + (v.length > 1 ? "s" : ""))
          .css("color", "#ffd180").attr("title", v.join("\n"));
    }
};

var update = function() {
    var amt = new AMT();
    _AMT.amt = amt;
    $("#title").text("loading...");
    amt.load(function() {
        var graph = amt.getGraph(_AMT.reasoning, false);
        graph.nodes = styleNodes(graph.nodes);
        graph.edges = styleEdges(graph.edges);

        _AMT.graph.nodes = new vis.DataSet(graph.nodes);
        _AMT.graph.edges = new vis.DataSet(graph.edges);
        if (_network) _network.destroy();
        _network = new vis.Network(
            document.getElementById("graph"),
            { nodes: _AMT.graph.nodes, edges: _AMT.graph.edges },
            AMT_VIS_OPTIONS
        );
        _AMT.thisNodes = graph.nodes;
        _AMT.thisEdges = graph.edges;

        $("#title").text(_AMT.title || "");
        showStatus(amt);
    });
};

// ------------------------------------------------------------
// Datasets: the examples listed in data/examples.json, and a file
// from the visitor's computer
// ------------------------------------------------------------
var _examples = [];

var loadExampleList = function(done) {
    fetch("../data/examples.json")
        .then(function(r) { return r.ok ? r.json() : []; })
        .catch(function() { return []; })
        .then(function(list) {
            _examples = list;
            var sel = $("#amt-viz").empty();
            list.forEach(function(ex) {
                sel.append($("<option>").val(ex.file).text(ex.title));
            });
            if (done) done();
        });
};

var chooseExample = function(file, fallbackTitle) {
    var title = fallbackTitle || file;
    _examples.forEach(function(ex) { if (ex.file === file) title = ex.title; });
    window.AMT_SOURCE = "../data/" + file;
    _AMT.title = title;
};

var reloadGraphWithProperties = function() {
    chooseExample($("#amt-viz").val());
    update();
    $("#graphPropModal").modal("close");
};

var loadLocalFile = function(input) {
    var file = input.files && input.files[0];
    if (!file) return;
    var reader = new FileReader();
    reader.onload = function() {
        window.AMT_SOURCE = { text: String(reader.result), name: file.name };
        _AMT.title = file.name;
        update();
        $("#graphPropModal").modal("close");
        input.value = "";
    };
    reader.readAsText(file);
};

// ------------------------------------------------------------
// UI handlers
// ------------------------------------------------------------
var toggleReasoning = function() {
    _AMT.reasoning = !_AMT.reasoning;
    $("#r-but").toggleClass("on", _AMT.reasoning).text(_AMT.reasoning ? "Reasoning: on" : "Reasoning: off");
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
        out += blank + " amt:weight    \"" + w + "\"^^<http://www.w3.org/2001/XMLSchema#decimal>" +
               (e.type ? " ;\r\n    <http://w3id.org/fw_ontology/hasType> <" + e.type + ">" : "") +
               (e.method ? " ;\r\n    <http://w3id.org/fw_ontology/hasMethod> <" + e.method + ">" : "") + " .\r\n";
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
    $("#rdfModal").modal({
        complete: function() { openRdfModal(true); }
    });
    $("#graphPropModal").modal({
        complete: function() { openGraphPropModal(true); }
    });
    loadExampleList(function() {
        // ?ttl=... or the default dataset; the title comes from the list when it is one of the examples
        var ttl = new URLSearchParams(window.location.search).get("ttl") || "";
        var file = ttl.replace(/^data\//, "");
        if (ttl) _AMT.title = file;
        else chooseExample("animals.ttl");
        _examples.forEach(function(ex) { if (ex.file === file) _AMT.title = ex.title; });
        $("#amt-viz").val(file || "animals.ttl");
        $("#amt-viz").material_select();
        update();
    });
});
