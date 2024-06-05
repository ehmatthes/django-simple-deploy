"""Coordinate integration for plugins that are installed by default."""

import pytest

from simple_deploy.plugins import pm

default_plugins = ["fly_io"]

def test_default_plugins():
    """Test all default plugins."""

    for plugin in default_plugins:
        print(f"Testing plugin: {plugin}")