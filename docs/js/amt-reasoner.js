// ============================================================
// AMT - Academic Meta Tool
// amt-reasoner.js - the reasoner of the Python engine, in JavaScript
//
// A line-by-line port of amt/logic.py and amt/reasoning.py (entailment
// reading, i.e. `minimal=False`). It works on plain objects and needs
// neither a DOM nor an RDF library, so the browser pages and
// tests/test_js_reasoner.py (Node) run the same code.
//
//   edge   { role, from, to, weight, inferred, provenance }
//   axiom  { type, iri, ... }   see normaliseAxioms()
//
// Loaded in the browser as window.AMTReasoner, in Node with require().
// ============================================================
(function (root, factory) {
  if (typeof module === "object" && module.exports) module.exports = factory();
  else root.AMTReasoner = factory();
})(typeof self !== "undefined" ? self : this, function () {
  "use strict";

  var AMT_NS = "http://academic-meta-tool.xyz/vocab#";

  var GOEDEL = AMT_NS + "GoedelLogic";
  var PRODUCT = AMT_NS + "ProductLogic";
  var LUKASIEWICZ = AMT_NS + "LukasiewiczLogic";
  var EINSTEIN = AMT_NS + "EinsteinProduct";
  var GEOMETRIC = AMT_NS + "GeometricMean";
  var HAMACHER = AMT_NS + "HamacherProduct";

  // ----------------------------------------------------------
  // Fuzzy logics (amt/logic.py)
  // ----------------------------------------------------------
  function einsteinPair(x, y) {
    var denom = 2.0 - (x + y - x * y);
    return denom === 0 ? 0.0 : (x * y) / denom;
  }

  function hamacherPair(x, y, gamma) {
    var denom = gamma + (1.0 - gamma) * (x + y - x * y);
    return denom === 0 ? 0.0 : (x * y) / denom;
  }

  function prod(ws) {
    var p = 1;
    for (var i = 0; i < ws.length; i++) p *= ws[i];
    return p;
  }

  function sum(ws) {
    var s = 0;
    for (var i = 0; i < ws.length; i++) s += ws[i];
    return s;
  }

  function fold(ws, fn) {
    var acc = ws[0];
    for (var i = 1; i < ws.length; i++) acc = fn(acc, ws[i]);
    return acc;
  }

  var REGISTRY = {};
  REGISTRY[GOEDEL] = { fn: function (ws) { return Math.min.apply(null, ws); }, arity: "binary", parametrised: false };
  REGISTRY[PRODUCT] = { fn: prod, arity: "binary", parametrised: false };
  REGISTRY[LUKASIEWICZ] = {
    fn: function (ws) { return Math.max(sum(ws) - (ws.length - 1), 0.0); },
    arity: "binary", parametrised: false,
  };
  REGISTRY[EINSTEIN] = { fn: function (ws) { return fold(ws, einsteinPair); }, arity: "binary", parametrised: false };
  REGISTRY[GEOMETRIC] = {
    fn: function (ws) { return Math.pow(prod(ws), 1.0 / ws.length); },
    arity: "n-ary", parametrised: false,
  };
  REGISTRY[HAMACHER] = {
    fn: function (ws, param) {
      if (param === null || param === undefined) {
        throw new Error("HamacherProduct requires amt:logicParameter (gamma). None was supplied.");
      }
      return fold(ws, function (a, b) { return hamacherPair(a, b, param); });
    },
    arity: "binary", parametrised: true,
  };

  // Python: round(max(0, min(1, raw)), 6)
  function round6(x) {
    return Number(x.toFixed(6));
  }

  function aggregate(weights, logicIri, parameter) {
    if (!weights || !weights.length) throw new Error("Cannot aggregate an empty weight list.");
    var spec = REGISTRY[logicIri];
    if (!spec) throw new Error("Unknown logic operator: " + logicIri);
    var raw = spec.fn(weights, parameter);
    return round6(Math.max(0.0, Math.min(1.0, raw)));
  }

  // ----------------------------------------------------------
  // Axioms: bring the loader's output into the engine's form
  // ----------------------------------------------------------
  function localName(iri) {
    return String(iri).split("/").pop().split("#").pop();
  }

  // `raw` entries come from a loader: { type, iri, <local name>: value, ... },
  // with `antecedents` already an array of role IRIs when the Turtle used an
  // RDF list. The legacy antecedent1/antecedent2 pair becomes a two-item list,
  // logicParameter becomes a number. Like the Python loader, the result is
  // sorted by type and IRI, which fixes the order of provenance lists.
  function normaliseAxioms(raw) {
    var out = raw.map(function (a) {
      var e = {};
      for (var k in a) e[k] = a[k];
      if (e.type === "RoleChainAxiom" && !e.antecedents) {
        e.antecedents = e.antecedent1 && e.antecedent2 ? [e.antecedent1, e.antecedent2] : [];
      }
      if (e.logicParameter !== undefined) {
        var f = parseFloat(e.logicParameter);
        if (!isNaN(f)) e.logicParameter = f;
      }
      return e;
    });
    out.sort(function (a, b) {
      var ta = AMT_NS + a.type, tb = AMT_NS + b.type;
      if (ta !== tb) return ta < tb ? -1 : 1;
      return a.iri < b.iri ? -1 : a.iri > b.iri ? 1 : 0;
    });
    return out;
  }

  // ----------------------------------------------------------
  // Live edge index (amt/reasoning.py: _EdgeIndex)
  // ----------------------------------------------------------
  function EdgeIndex(edges) {
    this.byKey = new Map();
    this.byRoleFrom = new Map();
    for (var i = 0; i < edges.length; i++) this.register(edges[i]);
  }
  EdgeIndex.prototype.register = function (e) {
    this.byKey.set(e.role + "\u0000" + e.from + "\u0000" + e.to, e);
    var starts = this.byRoleFrom.get(e.role);
    if (!starts) { starts = new Map(); this.byRoleFrom.set(e.role, starts); }
    var list = starts.get(e.from);
    if (!list) { list = []; starts.set(e.from, list); }
    list.push(e);
  };
  EdgeIndex.prototype.get = function (role, from, to) {
    return this.byKey.get(role + "\u0000" + from + "\u0000" + to) || null;
  };
  EdgeIndex.prototype.outgoing = function (role, from) {
    var starts = this.byRoleFrom.get(role);
    if (!starts) return [];
    return starts.get(from) || [];
  };
  EdgeIndex.prototype.starts = function (role) {
    var starts = this.byRoleFrom.get(role);
    if (!starts) return [];
    return Array.from(starts.entries());
  };
  EdgeIndex.prototype.append = function (result, edge) {
    result.push(edge);
    this.register(edge);
  };

  // ----------------------------------------------------------
  // Type and method (amt/fw.py)
  // ----------------------------------------------------------
  var FW_NS = "http://w3id.org/fw_ontology/";
  var VAGUENESS = FW_NS + "Vagueness";
  var UNCERTAINTY = FW_NS + "Uncertainty";
  var FUZZINESS_WOBBLINESS = FW_NS + "FuzzinessWobbliness";

  // The type that counts for an edge: its own, or vagueness (the default).
  function effectiveType(edge) { return (edge && edge.type) || VAGUENESS; }

  // The value to store in an edge: null for the default type.
  function storedType(t) { return !t || t === VAGUENESS ? null : t; }

  // Effective type of a statement derived from several others: the common
  // type if all agree, otherwise fw:FuzzinessWobbliness. null counts as vagueness.
  function combineTypes(types) {
    var seen = [];
    for (var i = 0; i < types.length; i++) {
      var t = types[i] || VAGUENESS;
      if (seen.indexOf(t) < 0) seen.push(t);
    }
    if (!seen.length) return VAGUENESS;
    return seen.length === 1 ? seen[0] : FUZZINESS_WOBBLINESS;
  }

  // Strings compare by UTF-16 code units here and by code points in Python;
  // IRIs are ASCII in practice, so the order is the same.
  function pathKey(method, type) { return [method || "", type]; }
  function keyLess(a, b) {
    if (a[0] !== b[0]) return a[0] < b[0];
    return a[1] < b[1];
  }

  function addOrStrengthen(result, index, role, from, to, weight, axiomIri, type, method) {
    type = type === undefined ? null : type;
    method = method === undefined ? null : method;
    var existing = index.get(role, from, to);
    if (!existing) {
      index.append(result, {
        role: role, from: from, to: to, weight: weight,
        inferred: true, provenance: axiomIri ? [axiomIri] : [],
        type: type, method: method, evidence: null,
      });
      return true;
    }
    var changed = false;
    if (axiomIri && existing.provenance.indexOf(axiomIri) < 0) {
      existing.provenance.push(axiomIri);
      changed = true;
    }
    if (existing.inferred) {
      if (existing.weight < weight) {
        existing.weight = weight;
        existing.type = type;
        existing.method = method;
        changed = true;
      } else if (existing.weight === weight) {
        // Equal weight: keep the path with the smaller (method, type). A
        // different type can change what depends on the edge, a different
        // method cannot.
        if (keyLess(pathKey(method, effectiveType({ type: type })), pathKey(existing.method, effectiveType(existing)))) {
          if (effectiveType({ type: type }) !== effectiveType(existing)) changed = true;
          existing.type = type;
          existing.method = method;
        }
      }
    }
    return changed;
  }

  function chainMatches(index, roles) {
    var matches = [];
    if (!roles.length) return matches;
    function extend(start, current, k, weights, edgesSoFar) {
      if (k === roles.length) {
        matches.push({ start: start, end: current, weights: weights, edges: edgesSoFar });
        return;
      }
      var next = index.outgoing(roles[k], current).slice();
      for (var i = 0; i < next.length; i++) {
        extend(start, next[i].to, k + 1, weights.concat([next[i].weight]), edgesSoFar.concat([next[i]]));
      }
    }
    var seeds = index.starts(roles[0]);
    for (var s = 0; s < seeds.length; s++) {
      var edges = seeds[s][1].slice();
      for (var i = 0; i < edges.length; i++) {
        extend(seeds[s][0], edges[i].to, 1, [edges[i].weight], [edges[i]]);
      }
    }
    return matches;
  }

  function applyRoleChain(result, axiom, index) {
    var ants = axiom.antecedents || [];
    if (!ants.length || !axiom.consequent || !axiom.logic) return false;
    var matches = chainMatches(index, ants);       // materialised before anything is added
    var changed = false;
    for (var i = 0; i < matches.length; i++) {
      var w = aggregate(matches[i].weights, axiom.logic, axiom.logicParameter);
      if (w <= 0) continue;
      var t = storedType(combineTypes(matches[i].edges.map(function (e) { return e.type; })));
      if (addOrStrengthen(result, index, axiom.consequent, matches[i].start, matches[i].end, w, axiom.iri || "", t, axiom.logic))
        changed = true;
    }
    return changed;
  }

  function applyInverse(result, axiom, index) {
    if (!axiom.antecedent || !axiom.inverse) return false;
    var changed = false;
    var starts = index.starts(axiom.antecedent);
    for (var s = 0; s < starts.length; s++) {
      var out = starts[s][1].slice();
      for (var i = 0; i < out.length; i++) {
        if (addOrStrengthen(result, index, axiom.inverse, out[i].to, out[i].from, out[i].weight, axiom.iri || "",
                            storedType(out[i].type), null))
          changed = true;
      }
    }
    return changed;
  }

  function applySubsumption(result, axiom, index) {
    var sub = axiom.subRole, sup = axiom.superRole;
    if (!sub || !sup || sub === sup) return false;
    var changed = false;
    var starts = index.starts(sub);
    for (var s = 0; s < starts.length; s++) {
      var out = starts[s][1].slice();
      for (var i = 0; i < out.length; i++) {
        if (addOrStrengthen(result, index, sup, out[i].from, out[i].to, out[i].weight, axiom.iri || "",
                            storedType(out[i].type), null))
          changed = true;
      }
    }
    return changed;
  }

  // ----------------------------------------------------------
  // Public: reason() and checkConsistency()
  // ----------------------------------------------------------
  // Returns { edges, stats }. The input edges are not changed.
  function reason(edges, axioms, options) {
    var maxIterations = (options && options.maxIterations) || 100;
    var result = edges.map(function (e) {
      return {
        role: e.role, from: e.from, to: e.to, weight: e.weight,
        inferred: !!e.inferred, provenance: (e.provenance || []).slice(),
        type: e.type || null, method: e.method || null, evidence: e.evidence || null,
      };
    });
    var index = new EdgeIndex(result);
    var iterations = 0, reached = false;
    for (var n = 0; n < maxIterations; n++) {
      iterations++;
      var changed = false;
      for (var i = 0; i < axioms.length; i++) {
        var a = axioms[i];
        if (a.type === "RoleChainAxiom") changed = applyRoleChain(result, a, index) || changed;
        else if (a.type === "InverseAxiom") changed = applyInverse(result, a, index) || changed;
        else if (a.type === "SubsumptionAxiom") changed = applySubsumption(result, a, index) || changed;
      }
      if (!changed) { reached = true; break; }
    }
    return { edges: result, stats: { iterations: iterations, suppressed: 0, reached_fixpoint: reached } };
  }

  // Returns { consistent, violations } with the same messages as Python.
  function checkConsistency(edges, axioms, reasoned) {
    if (!reasoned) reasoned = reason(edges, axioms).edges;
    var violations = [];
    var keys = new Set(reasoned.map(function (e) { return e.role + "\u0000" + e.from + "\u0000" + e.to; }));
    for (var i = 0; i < axioms.length; i++) {
      var a = axioms[i];
      if (a.type === "DisjointAxiom") {
        for (var j = 0; j < reasoned.length; j++) {
          var e = reasoned[j];
          if (e.role === a.role1 && keys.has(a.role2 + "\u0000" + e.from + "\u0000" + e.to)) {
            violations.push("DisjointAxiom violated: " + localName(e.from) + " has both " +
              localName(a.role1) + " and " + localName(a.role2) + " to " + localName(e.to));
          }
        }
      } else if (a.type === "SelfDisjointAxiom") {
        for (var k = 0; k < reasoned.length; k++) {
          var f = reasoned[k];
          if (f.role === a.role && f.from === f.to) {
            violations.push("SelfDisjointAxiom violated: " + localName(f.from) +
              " has self-loop via " + localName(a.role));
          }
        }
      }
    }
    return { consistent: violations.length === 0, violations: violations };
  }

  return {
    AMT_NS: AMT_NS,
    LOGICS: REGISTRY,
    FW_NS: FW_NS,
    VAGUENESS: VAGUENESS,
    UNCERTAINTY: UNCERTAINTY,
    FUZZINESS_WOBBLINESS: FUZZINESS_WOBBLINESS,
    effectiveType: effectiveType,
    storedType: storedType,
    combineTypes: combineTypes,
    aggregate: aggregate,
    normaliseAxioms: normaliseAxioms,
    reason: reason,
    checkConsistency: checkConsistency,
  };
});
