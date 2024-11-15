"""Test a single platform's deployment.

This runs the root e2e_tests/conftest.py, and then runs the platform-specific deployment test function.
"""

from pathlib import Path
import importlib
import sys

import pytest


def test_platform_deployment(tmp_project, cli_options, request):
    """Test full deployment of the given platform."""

    # The tests/ dir is not part of the plugin package, so it needs to be added
    # to sys.path.
    plugin_spec = importlib.util.find_spec(cli_options.plugin_name)
    assert plugin_spec

    plugin_tests_path = Path(plugin_spec.origin).parents[1] / "tests"
    assert plugin_tests_path.exists()

    sys.path.insert(0, plugin_tests_path.as_posix())

    # Load the plugin's e2e test module.
    plugin_e2e_path = plugin_tests_path / "e2e_tests" / "test_deployment"
    module_path = "e2e_tests.test_deployment"
    platform_e2e_module = importlib.import_module(module_path)

    # Call the e2e test function.
    platform_e2e_module.test_deployment(tmp_project, cli_options, request)
