#!/usr/bin/env python3
"""
main.py — the development pipeline of AMT.engine.

This is the maintenance entry point of the repository: tests, ontology
checks, example runs, determinism check, docs sync. It does *not* replace the
product commands ``amt`` and ``amt-runner``; those stay exactly as they are.

    python main.py                     all steps, in order
    python main.py --list              print steps and exit
    python main.py --only tests        one step
    python main.py --from examples     this step and everything after
    python main.py --skip determinism  everything but this step
    python main.py --dry-run           print the plan, run nothing
    python main.py --strict            warnings become errors (what CI runs)

Every step is also runnable on its own, e.g. ``python py/step_tests.py``.
The combined output is written to ``build/pipeline_report.txt``. Step
modules are started as child processes, so ``--list`` and ``--dry-run``
import nothing heavy (no rdflib, no pyshacl).
"""
from __future__ import annotations

import argparse
import os
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent
PY_DIR = ROOT / "py"
REPORT = ROOT / "build" / "pipeline_report.txt"

# (name, script, what it checks)
STEPS: list[tuple[str, str, str]] = [
    ("meta",        "step_meta.py",        "version, date and changelog agree across all files"),
    ("ontology",    "step_ontology.py",    "bundled SHACL examples validate as documented"),
    ("site",        "step_site.py",        "start, vocabulary and ontology pages, amt.rdf and figures generated from ontology/amt.ttl"),
    ("tests",       "step_tests.py",       "pytest suite in tests/"),
    ("examples",    "step_examples.py",    "every examples/*.ttl runs through the full pipeline"),
    ("determinism", "step_determinism.py", "two runs under different hash seeds give identical bytes"),
    ("docs-sync",   "step_docs_sync.py",   "examples/*.ttl copied to docs/data/ (a change fails with --strict)"),
]
NAMES = [s[0] for s in STEPS]


def select(args: argparse.Namespace) -> list[tuple[str, str, str]]:
    chosen = list(STEPS)
    if args.only:
        chosen = [s for s in chosen if s[0] == args.only]
    if args.from_step:
        start = NAMES.index(args.from_step)
        chosen = [s for s in chosen if NAMES.index(s[0]) >= start]
    if args.skip:
        chosen = [s for s in chosen if s[0] not in args.skip]
    return chosen


def run_step(name: str, script: str, strict: bool, log) -> tuple[int, float]:
    env = dict(os.environ)
    # Without this, check marks and arrows fail at the pipe on Windows.
    env["PYTHONIOENCODING"] = "utf-8"
    env["AMT_DEV_STRICT"] = "1" if strict else "0"
    started = time.perf_counter()
    proc = subprocess.Popen(
        [sys.executable, str(PY_DIR / script)],
        cwd=ROOT, env=env, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
        text=True, encoding="utf-8", errors="replace",
    )
    assert proc.stdout is not None
    for line in proc.stdout:
        emit(f"     {line.rstrip()}", log)
    code = proc.wait()
    return code, time.perf_counter() - started


def emit(line: str, log) -> None:
    print(line)
    if log is not None:
        log.write(line + "\n")


def main(argv: list[str] | None = None) -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")

    p = argparse.ArgumentParser(description="Development pipeline of AMT.engine")
    p.add_argument("--list", action="store_true", help="print steps and exit")
    p.add_argument("--only", choices=NAMES, metavar="STEP", help="run one step")
    p.add_argument("--from", dest="from_step", choices=NAMES, metavar="STEP",
                   help="run this step and everything after it")
    p.add_argument("--skip", action="append", choices=NAMES, metavar="STEP",
                   help="skip a step (repeatable)")
    p.add_argument("--dry-run", action="store_true", help="print the plan, run nothing")
    p.add_argument("--strict", action="store_true", help="warnings become errors")
    args = p.parse_args(argv)

    if args.list:
        width = max(len(n) for n in NAMES)
        for name, script, what in STEPS:
            print(f"{name:<{width}}  py/{script:<22} {what}")
        return 0

    chosen = select(args)
    if not chosen:
        print("Nothing selected.")
        return 0

    if args.dry_run:
        print("Plan (dry run, nothing is executed):")
        for i, (name, script, _) in enumerate(chosen, 1):
            print(f"  {i}. {name:<12} py/{script}")
        print(f"strict: {'yes' if args.strict else 'no'}")
        return 0

    REPORT.parent.mkdir(parents=True, exist_ok=True)
    timings: list[tuple[str, float, int]] = []
    with REPORT.open("w", encoding="utf-8") as log:
        for i, (name, script, _) in enumerate(chosen, 1):
            emit(f"[{i}/{len(chosen)}] {name}", log)
            code, secs = run_step(name, script, args.strict, log)
            timings.append((name, secs, code))
            if code != 0:
                emit(f"     step '{name}' failed (exit {code}); stopping.", log)
                break

        total = sum(t[1] for t in timings) or 1.0
        emit("", log)
        emit(f"{'step':<12} {'seconds':>8} {'share':>7}  result", log)
        for name, secs, code in timings:
            emit(f"{name:<12} {secs:>8.1f} {secs / total:>6.0%}  {'ok' if code == 0 else 'FAILED'}", log)
        emit(f"{'total':<12} {total:>8.1f}", log)

    failed = any(code != 0 for _, _, code in timings)
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
