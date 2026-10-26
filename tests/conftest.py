"""Make the development helpers in ``py/`` importable from the tests.

pytest ships a module called ``py``, which shadows the repository's ``py/``
folder as a package. Adding the folder itself to the import path sidesteps
that: the helpers are imported by their file names, as the pipeline does.
"""
import sys
from pathlib import Path

PY_DIR = Path(__file__).resolve().parent.parent / "py"
if str(PY_DIR) not in sys.path:
    sys.path.insert(0, str(PY_DIR))
