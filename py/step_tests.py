"""
Step ``tests`` — the pytest suite in ``tests/``.

Warnings from rdflib's deprecation notices are suppressed in the output;
they are tens of thousands of lines and bury the one that matters.

Standalone:  python py/step_tests.py
"""
from __future__ import annotations

import sys

try:
    from amt_dev_utils import Report, run_python
except ImportError:
    from py.amt_dev_utils import Report, run_python


def main() -> int:
    rep = Report("tests")
    code = run_python(["-m", "pytest", "tests", "-q", "--disable-warnings", "-p", "no:cacheprovider"])
    if code != 0:
        return rep.fail(f"pytest exited with {code}")
    rep.ok("test suite green")
    return rep.finish()


if __name__ == "__main__":
    sys.exit(main())
