"""
Step ``determinism`` — the same input gives the same bytes.

Runs the pipeline twice on two examples under *different* ``PYTHONHASHSEED``
values and compares the outputs byte for byte. The seed matters: rule
application once iterated a Python ``set``, so provenance lists came out in
an order that depended on string hashing, and three of the six exported
files differed between otherwise identical runs (fixed in 0.3.0). Two runs
with the same seed would never have caught that.

``*.report.md`` is excluded on purpose: it records when the run started and
finished. Beschluss 2026-10-26 (PRIMER.md, A4): run-time reports keep their
clock, because they describe a run and are not a versioned artefact.

Standalone:  python py/step_determinism.py
"""
from __future__ import annotations

import filecmp
import shutil
import sys

try:
    from amt_dev_utils import DETERMINISM_DIR, EXAMPLES_DIR, ROOT, Report, ensure_dirs, run_python
except ImportError:
    from py.amt_dev_utils import DETERMINISM_DIR, EXAMPLES_DIR, ROOT, Report, ensure_dirs, run_python

SAMPLES = ("animals.ttl", "subsumption-demo.ttl", "hextuple-demo.ttl")
SEEDS = ("1", "2")
EXCLUDED_SUFFIX = ".report.md"


def main() -> int:
    rep = Report("determinism")
    ensure_dirs()
    if DETERMINISM_DIR.exists():
        shutil.rmtree(DETERMINISM_DIR)
    DETERMINISM_DIR.mkdir(parents=True)

    for name in SAMPLES:
        src = EXAMPLES_DIR / name
        if not src.exists():
            return rep.fail(f"{name} not found in examples/")
        outs = []
        for seed in SEEDS:
            out = DETERMINISM_DIR / f"{src.stem}-seed{seed}"
            code = run_python(
                ["-m", "amt.runner", src.relative_to(ROOT).as_posix(),
                 "-o", out.relative_to(ROOT).as_posix(), "--no-info"],
                env_extra={"PYTHONHASHSEED": seed},
            )
            if code != 0:
                return rep.fail(f"{name} (PYTHONHASHSEED={seed}): amt.runner exited with {code}")
            outs.append(out)

        first, second = outs
        files = sorted(p.name for p in first.iterdir() if not p.name.endswith(EXCLUDED_SUFFIX))
        different = [
            f for f in files
            if not (second / f).exists() or not filecmp.cmp(first / f, second / f, shallow=False)
        ]
        if different:
            return rep.fail(f"{name}: differs between PYTHONHASHSEED values: {', '.join(different)}")
        rep.ok(f"{name}: {len(files)} file(s) byte-identical across seeds {SEEDS[0]} and {SEEDS[1]}")
    return rep.finish()


if __name__ == "__main__":
    sys.exit(main())
