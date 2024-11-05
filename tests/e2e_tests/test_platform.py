"""Test a single platform's deployment.

This runs the root e2e_tests/conftest.py, and then runs the platform-specific deployment test function.
"""

from pathlib import Path
import importlib

import pytest


def test_platform_deployment(tmp_project, cli_options, request):
    """Test full deployment of the given platform."""
    # module_path = f"simple_deploy.management.commands.{cli_options.platform}.tests.e2e_tests.test_deployment"

    # Find the plugin's e2e_tests directory.
    path = Path(request.module.__file__)
    while path.name != "e2e_tests":
        path = path.parent
    e2e_tests_path = path
    module_path = (e2e_tests_path / "test_deployment").as_posix()




    platform_e2e_module = importlib.import_module(module_path)
    platform_e2e_module.test_deployment(tmp_project, cli_options, request)
