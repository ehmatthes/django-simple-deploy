"""Root conftest.py"""

import sys
import os
from pathlib import Path
from importlib.metadata import packages_distributions
import importlib

import pytest

# Don't look at any test files in the sample_project/ dir.
collect_ignore = ["sample_project", "tests/e2e_tests"]

# Let plugins import utilities.
path = Path(__file__).parent / "tests" / "integration_tests" / "utils"
sys.path.insert(0, str(path))

# Get names of all plugins.
# plugin_names = packages_distributions().keys()
# plugin_names = [p for p in plugin_names if p.startswith("dsd_")]

# # Find paths to all plugins.
# plugin_paths = []
# for plugin in plugin_names:
#     plugin_spec = importlib.util.find_spec(plugin)
#     plugin_path = Path(plugin_spec.origin).parents[1]
#     plugin_paths.append(plugin_path)

# plugin_e2e_paths = [p / "tests/e2e_tests" for p in plugin_paths]


# def pytest_collect_directory(path, parent)


# Run tests for all installed plugins.
# print(sys.path)
# for plugin_path in plugin_paths:
#     if plugin_path.exists():
#         sys.path.insert(0, str(plugin_path))
# print(sys.path)

# If not running e2e tests, ignore entire e2e_tests directory.
# running_e2e = any(["e2e_tests" in arg for arg in sys.argv])
# if not running_e2e:
#     collect_ignore.append("tests/e2e_tests")
    # collect_ignore.append(plugin_e2e_paths_rel[0])
    # collect_ignore.append(plugin_e2e_paths_rel[1])
    # collect_ignore.append(plugin_e2e_paths_rel[2])

# def pytest_collection_modifyitems(config, items):
#     collected_modules = set([item.fspath for item in items])
#     for cm in collected_modules:
#         print("cm", cm)

#     print(len(items))

    # sys.exit()