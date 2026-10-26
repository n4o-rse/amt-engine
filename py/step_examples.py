"""
Step ``examples`` — every file in ``examples/`` runs through the full pipeline.

Each ``examples/*.ttl`` goes through ``amt.runner`` (validate, reason, check,
export) into ``build/examples/<stem>/``. A non-zero exit from the runner means
the example no longer works against the engine, which is exactly what a
documented example must not do.

Standalone:  python py/step_examples.py
"""
from __future__ import annotations

import sys

try:
    from amt_dev_utils import EXAMPLES_DIR, EXAMPLES_OUT_DIR, ROOT, Report, ensure_dirs, run_python
except ImportError:
    from py.amt_dev_utils import EXAMPLES_DIR, EXAMPLES_OUT_DIR, ROOT, Report, ensure_dirs, run_python

EXPECTED_OUTPUTS = ("reasoned.ttl", "cypher", "nodes.csv", "edges.csv", "html", "report.md")


def main() -> int:
    rep = Report("examples")
    ensure_dirs()
    sources = sorted(EXAMPLES_DIR.glob("*.ttl"))
    if not sources:
        return rep.fail("no examples/*.ttl found")

    failed = 0
    for src in sources:
        out = EXAMPLES_OUT_DIR / src.stem
        print(f"RUN  {src.relative_to(ROOT).as_posix()} -> {out.relative_to(ROOT).as_posix()}/")
        code = run_python(
            ["-m", "amt.runner", src.relative_to(ROOT).as_posix(),
             "-o", out.relative_to(ROOT).as_posix(), "--no-info"]
        )
        if code != 0:
            print(f"FAIL {src.name}: amt.runner exited with {code}")
            failed += 1
            continue
        missing = [e for e in EXPECTED_OUTPUTS if not (out / f"{src.stem}.{e}").exists()]
        if missing:
            rep.warn(f"{src.name}: missing outputs {', '.join(missing)}")

    if failed:
        return rep.fail(f"{failed} of {len(sources)} example(s) failed")
    rep.ok(f"{len(sources)} example(s) ran through the full pipeline")
    return rep.finish()


if __name__ == "__main__":
    sys.exit(main())
