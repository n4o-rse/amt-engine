"""
Step ``ontology`` — the bundled SHACL examples behave as documented.

Runs ``ontology/validate_examples.py``, which checks that
``example-valid.ttl`` passes the shapes and ``example-invalid.ttl`` is
rejected. The script exits non-zero when either expectation is not met.

Standalone:  python py/step_ontology.py
"""
from __future__ import annotations

import sys

try:
    from amt_dev_utils import ONTOLOGY_DIR, ROOT, Report, run_python
except ImportError:
    from py.amt_dev_utils import ONTOLOGY_DIR, ROOT, Report, run_python


def main() -> int:
    rep = Report("ontology")
    script = ONTOLOGY_DIR / "validate_examples.py"
    if not script.exists():
        return rep.fail(f"{script.relative_to(ROOT)} not found")
    code = run_python([str(script.relative_to(ROOT))])
    if code != 0:
        return rep.fail(f"validate_examples.py exited with {code}")
    rep.ok("ontology examples validate as expected")
    return rep.finish()


if __name__ == "__main__":
    sys.exit(main())
