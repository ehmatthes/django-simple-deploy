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



# Get names of all plugins.
plugin_names = packages_distributions().keys()
plugin_names = [p for p in plugin_names if p.startswith("dsd_")]

default_plugin_names = ["dsd_flyio", "dsd_platformsh"]
nd_plugin_names = [p for p in plugin_names if p not in default_plugin_names]

nd_plugin_paths = []
for nd_plugin_name in nd_plugin_names:
    spec = importlib.util.find_spec(nd_plugin_name)
    path = Path(spec.origin).parents[1]
    nd_plugin_paths.append(path)

sd_root_dir = Path(__file__).parent
nd_plugin_paths_rel = []
for path in nd_plugin_paths:
    path_rel = os.path.relpath(path, sd_root_dir)
    path_rel = Path(path_rel) / "tests"
    nd_plugin_paths_rel.append(str(path_rel))

print(nd_plugin_paths)
print(nd_plugin_paths_rel)

def pytest_configure(config):
    # print("\n*** in config ***")
    # print(config)
    # config.args.append("../dsd-heroku/tests/")
    config.args.append("/Users/eric/projects/dsd-heroku/tests/")
    # breakpoint()
    # sys.exit()


# for path in nd_plugin_paths_rel:
# sys.exit()

def pytest_collection_modifyitems(config, items):
    # Convert relative paths to absolute paths based on root directory
    root_dir = Path(config.rootdir)
    absolute_plugin_paths = [root_dir / Path(p).resolve() for p in nd_plugin_paths_rel]

    # Filter and add items from these paths if they’re part of the collected items
    new_items = []
    for item in items:
        item_path = Path(item.fspath).resolve()
        if any(item_path.is_relative_to(abs_path) for abs_path in absolute_plugin_paths):
            new_items.append(item)

    # Add new items to the collection
    items.extend(new_items)

    # Optional: Print the added items for verification
    print("Dynamically added plugin tests:")
    for item in new_items:
        print(item.nodeid)