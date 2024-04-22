"""Root conftest.py"""

import sys


# Don't look at any test files in the sample_project/ dir.
collect_ignore = ["sample_project"]

# If not running an e2e test, completely ignore those tests.
if "e2e_tests" not in sys.argv:
    collect_ignore.append("tests/e2e_tests")