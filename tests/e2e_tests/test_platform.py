"""Test a single platform's deployment.

This runs the root e2e_tests/conftest.py, and then runs the platform-specific deployment test function.
"""

from pathlib import Path
import importlib
import sys

import pytest


def test_platform_deployment(tmp_project, cli_options, request):
    """Test full deployment of the given platform."""
    # module_path = f"simple_deploy.management.commands.{cli_options.platform}.tests.e2e_tests.test_deployment"
    # sd_root_dir = Path(__file__).parent.parent.parent

    # # Find the plugin's e2e_tests directory. Can't use request.module.__file__,
    # # because that points to core's test_platform.py.
    # # Assume plugin is in a repo called dsd-<something>, in same directory as
    # # django-simple-deploy.
    # plugin_e2e_dir = sd_root_dir.parent / cli_options.plugin_name / "tests/e2e_tests"
    # assert plugin_e2e_dir.exists()

    # file_path = plugin_e2e_dir / "test_deployment.py"
    # assert file_path.exists()

    # module_path = (plugin_e2e_dir / "test_deployment")

    # The tests/ dir is not part of the plugin package, so it needs to be added
    # to sys.path.
    plugin_spec = importlib.util.find_spec(cli_options.plugin_name)
    plugin_tests_path = Path(plugin_spec.origin).parents[1] / "tests"
    assert plugin_tests_path.exists()
    sys.path.insert(0, plugin_tests_path.as_posix())

    plugin_e2e_path = plugin_tests_path / "e2e_tests" / "test_deployment"
    # print("pep", plugin_e2e_path)
    # assert plugin_e2e_path.exists()
    module_path = "e2e_tests.test_deployment"

    # platform_e2e_module = importlib.import_module(plugin_e2e_path.as_posix())
    platform_e2e_module = importlib.import_module(module_path)
    platform_e2e_module.test_deployment(tmp_project, cli_options, request)







    # module_path = f"{cli_options.plugin_name}.tests.e2e_tests.test_deployment"
    # import sys
    # print("sp", sys.path)

    # from importlib.metadata import packages_distributions as pd
    # assert cli_options.plugin_name in pd().keys()

    # # platform_e2e_module = importlib.import_module(module_path.as_posix())
    # platform_e2e_module = importlib.import_module(module_path)
    # platform_e2e_module.test_deployment(tmp_project, cli_options, request)
