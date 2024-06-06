"""Root conftest.py"""

import sys
from pathlib import Path

import pytest

# Let plugins import utilities.
path = Path(__file__).parent / "tests" / "integration_tests" / "utils"
sys.path.insert(0, path)


# Don't look at any test files in the sample_project/ dir.
collect_ignore = ["sample_project"]

# If not running an e2e test, completely ignore those tests.
if "e2e_tests" not in sys.argv:
    collect_ignore.append("tests/e2e_tests")


# If running a plugin's e2e tests, run the e2e_tests conftest?
running_e2e = any(["e2e_tests" in arg for arg in sys.argv])
if running_e2e:
    import tests.e2e_tests.conftest as e2e_conftest

    def pytest_configure(config):
        if not e2e_conftest.check_valid_call(config):
            pytest.exit("Invalid command for e2e testing.")