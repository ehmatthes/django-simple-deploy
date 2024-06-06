"""Root conftest.py"""

import sys
from pathlib import Path

import pytest

# Let plugins import utilities.
path = Path(__file__).parent / "tests" / "integration_tests" / "utils"
sys.path.insert(0, path)


# Don't look at any test files in the sample_project/ dir.
collect_ignore = ["sample_project"]


# If not running e2e tests, ignore entire e2e_tests as well.
# DEV: This can be simplified with all e2e tests moved to plugin dirs.
running_e2e = any(["e2e_tests" in arg for arg in sys.argv])
if not running_e2e:
    collect_ignore.append("tests/e2e_tests")
else:
    collect_ignore.append("tests/e2e_tests/platforms")