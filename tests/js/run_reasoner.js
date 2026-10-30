// Reads {"op": ..., ...} as JSON on stdin, writes the result as JSON on stdout.
// Used by tests/test_js_reasoner.py to compare docs/js/amt-reasoner.js with the Python engine.
const path = require("path");
const R = require(path.join(__dirname, "..", "..", "docs", "js", "amt-reasoner.js"));

let input = "";
process.stdin.setEncoding("utf8");
process.stdin.on("data", (c) => (input += c));
process.stdin.on("end", () => {
  const req = JSON.parse(input);
  let out;
  if (req.op === "aggregate") {
    out = req.cases.map((c) => R.aggregate(c.weights, c.logic, c.parameter === undefined ? null : c.parameter));
  } else if (req.op === "reason") {
    const r = R.reason(req.edges, req.axioms);
    out = { edges: r.edges, stats: r.stats, consistency: R.checkConsistency(req.edges, req.axioms, r.edges) };
  } else if (req.op === "combine") {
    out = req.cases.map((c) => R.combineTypes(c));
  } else if (req.op === "normalise") {
    out = R.normaliseAxioms(req.axioms);
  } else {
    throw new Error("unknown op " + req.op);
  }
  process.stdout.write(JSON.stringify(out));
});
