"""Utils for finding resources from plugins."""

import os
from pathlib import Path
from importlib.metadata import packages_distributions
import importlib


def get_plugin_paths_rel():
    """Get relative paths to all plugins."""

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

        if not path_rel.exists():
            # This block is hit when a plugin is installed through PyPI rather than
            # a local editable install. PyPI versions typically don't have tests.
            continue

        plugin_paths_rel.append(str(path_rel))

    return plugin_paths
