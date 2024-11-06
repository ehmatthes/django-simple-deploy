"""Root conftest.py"""

import sys
import os
from pathlib import Path
from importlib.metadata import packages_distributions
import importlib

import pytest

# Don't look at any test files in the sample_project/ dir.
collect_ignore = ["sample_project"]

# Let plugins import utilities.
path = Path(__file__).parent / "tests" / "integration_tests" / "utils"
sys.path.insert(0, path)

# Get names of all plugins.
plugin_names = packages_distributions().keys()
plugin_names = [p for p in plugin_names if p.startswith("dsd_")]

# Find paths to all plugin_names' e2e tests.
plugin_test_paths = []
plugin_e2e_paths = []
for plugin in plugin_names:
    plugin_spec = importlib.util.find_spec(plugin)
    plugin_test_path = Path(plugin_spec.origin).parents[1] / "tests"
    plugin_e2e_path = Path(plugin_spec.origin).parents[1] / "tests" / "e2e_tests"
    plugin_test_paths.append(plugin_test_path)
    plugin_e2e_paths.append(plugin_e2e_path)

# Run tests for all installed plugins.
for plugin_test_path in plugin_test_paths:
    if plugin_test_path.exists():
        sys.path.insert(0, str(plugin_test_path))
        print("here")
    else:
        print("HERE")

# # Find relative paths to all plugin e2e tests.
# plugin_e2e_paths_rel = []
# path_current = Path(__file__).parent
# for path in plugin_e2e_paths:
#     path_rel = os.path.relpath(path, path_current)
#     plugin_e2e_paths_rel.append(path_rel)

# If not running e2e tests, ignore entire e2e_tests directory.
running_e2e = any(["e2e_tests" in arg for arg in sys.argv])
if not running_e2e:
    collect_ignore.append("tests/e2e_tests")
    # collect_ignore.append(plugin_e2e_paths_rel[0])
    # collect_ignore.append(plugin_e2e_paths_rel[1])
    # collect_ignore.append(plugin_e2e_paths_rel[2])



# def pytest_collection_modifyitems(config, items):
#     print("\nCollected Tests:")
#     for item in items:
#         print(item.nodeid)

# def pytest_collection_modifyitems(config, items):
#     # No need to modify items if explicitly running an e2e test.
#     if running_e2e:
#         return

#     kept_items = []
#     plugin_e2e_paths_str = [str(p) for p in plugin_e2e_paths]
#     for item in items:
#         item_path = str(Path(item.fspath).resolve())
#         if any()
#         print(item_path, type(item_path))

#     sys.exit()

# print(collect_ignore)
# for p in collect_ignore:
#     print(p)
# sys.exit()

def pytest_collection_modifyitems(config, items):
    collected_modules = set([item.fspath for item in items])
    for cm in collected_modules:
        print("cm", cm)
    # for item in items:
    #     print(item.fspath, item.name)
    print(len(items))
    sys.exit()