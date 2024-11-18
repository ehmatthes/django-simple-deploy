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

    # DEV: It's probably better to use absolute paths, and make sure any path
    # that's already included in args isn't appended again. This would mean
    # comparing each plugin path to each arg, probably with path.resolve(), and
    # only adding if not already in args. Consider working with
    # config._inicache["testpaths"] for this.
    #
    # Also, consider bailing if there are already any of these paths in config.args.
    # We don't want to run all plugins' tests if the user is just trying to run tests
    # for a single plugin.

    # Don't add paths that have already been explicitly included.
    # DEV: Commented out in order to avoid running plugin tests temporarily.
    # plugin_paths_rel = plugin_finders.get_plugin_paths_rel()
    # for path in plugin_paths_rel:
    #     if path not in config.args:
    #         config.args.append(path)




    plugin_paths_rel = plugin_finders.get_plugin_paths_rel()
    unit_test_paths = [p / "tests" / "unit_tests" for p in plugin_paths_rel]

    breakpoint()

    for path in unit_test_paths:
        if not path.exists():
            continue

        if path not in config.args:
            config.args.append(path.as_posix())

    breakpoint()