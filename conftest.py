"""Root conftest.py"""

import sys
import os
from pathlib import Path
from importlib.metadata import packages_distributions
import importlib

import pytest

# Don't look at any test files in the sample_project/ dir.
# Don't collect e2e tests; only run when specified over CLI.
collect_ignore = ["sample_project", "tests/e2e_tests"]

# Let plugins import utilities.
path = Path(__file__).parent / "tests" / "integration_tests" / "utils"
sys.path.insert(0, str(path))


# --- Dynamically import tests from all installed plugins ---

# Get names of all plugins.
plugin_names = packages_distributions().keys()
plugin_names = [p for p in plugin_names if p.startswith("dsd_")]

plugin_paths = []
for plugin_name in plugin_names:
    spec = importlib.util.find_spec(plugin_name)
    path = Path(spec.origin).parents[1]
    plugin_paths.append(path)

sd_root_dir = Path(__file__).parent
plugin_paths_rel = []
for path in plugin_paths:
    path_rel = os.path.relpath(path, sd_root_dir)
    path_rel = Path(path_rel) / "tests"
    plugin_paths_rel.append(str(path_rel))

def pytest_configure(config):
    """Add plugin test paths to what's being collected."""

    # Don't modify test collection if running an e2e test.
    for arg in config.args:
        if "e2e_tests" in arg:
            return

    # DEV: It's probably better to use absolute paths, and make sure any path
    # that's already included in args isn't appended again. This would mean
    # comparing each plugin path to each arg, probably with path.resolve(), and
    # only adding if not already in args.

    # Don't add paths that have already been explicitly included.
    for path in plugin_paths_rel:
        if path not in config.args:
            config.args.append(path)
