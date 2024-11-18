"""Root conftest.py"""

import sys
import os
from pathlib import Path
from importlib.metadata import packages_distributions
import importlib

import pytest

from tests.utils import plugin_finders


# Don't look at any test files in the sample_project/ dir.
# Don't collect e2e tests; only run when specified over CLI.
collect_ignore = ["sample_project", "tests/e2e_tests"]

# Let plugins import utilities.
path = Path(__file__).parent / "tests" / "integration_tests" / "utils"
sys.path.insert(0, str(path))


def pytest_configure(config):
    """Add plugin test paths to what's being collected."""

    # Don't modify test collection when running e2e tests.
    if any("e2e_tests" in arg for arg in config.args):
        return

    # Define expected unit and integration tests paths for plugins.
    plugin_paths_rel = plugin_finders.get_plugin_paths_rel()
    unit_test_paths = [p / "tests" / "unit_tests" for p in plugin_paths_rel]
    int_test_paths = [p / "tests" / "integration_tests" for p in plugin_paths_rel]

    # Want to know if unit or integration tests were explicitly called.
    unit_tests_explicit = any(arg.endswith("tests/unit_tests") for arg in sys.argv)
    int_tests_explicit = any(arg.endswith("tests/integration_tests") for arg in sys.argv)

    # Consider a "bare" call one that doesn't explicitly ask for unit or integration tests.
    # In this case, we want to collect all plugin tests. Look at all args beyond
    # pytest command, and see if any paths are included.
    bare_call = True
    for arg in sys.argv[1:]:
        if Path(arg).exists():
            bare_call = False
            break

    # Collect appropriate tests from plugins.
    if unit_tests_explicit or bare_call:
        # Collect plugins' unit tests.
        for path in unit_test_paths:
            if path.exists() and path not in config.args:
                config.args.append(path.as_posix())

    if int_tests_explicit or bare_call:
        # Collect plugins' integration tests.
        for path in int_test_paths:
            if path.exists() and path not in config.args:
                config.args.append(path.as_posix())
