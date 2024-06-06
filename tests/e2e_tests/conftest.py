"""Configuration for e2e tests."""

import sys, importlib
from pathlib import Path

import pytest

from tests.e2e_tests.utils import manage_sample_project as msp
from tests.e2e_tests.utils.it_helper_functions import confirm_destroy_project


# --- Validity check ---


def check_valid_call(config):
    """Make sure the test call is valid for current e2e tests.

    e2e tests create remote resources on the user's account, which can accrue charges.
    For now, these must be run separately from local tests, and in a controlled manner.

    Requires -s flag; there's information during the deployment that really should be
    displayed as the test progresses.
    """
    if not config.getoption("-s") == "no":
        msg = "You must use the `-s` or `--capture=no` flag when running e2e tests."
        print(msg)
        return False

    # Make sure unit tests or integration tests aren't being run as well.
    if "unit_tests" in " ".join(config.args) or "integration_tests" in " ".join(
        config.args
    ):
        msg = "Unit and integration tests should be run separate from e2e tests."
        print(msg)
        return False

    # No obvious reason not to run e2e tests.
    return True


def pytest_configure(config):
    if not check_valid_call(config):
        pytest.exit("Invalid command for e2e testing.")


# --- CLI args ---


def pytest_addoption(parser):
    parser.addoption(
        "--pkg-manager",
        action="store",
        default="req_txt",
        help="Approach for dependency management: defaults to 'req_txt'",
    )
    parser.addoption(
        "--pypi",
        action="store_true",
        default=False,
        help="Test the PyPI version of simple_deploy.",
    )
    parser.addoption(
        "--automate-all",
        action="store_true",
        default=False,
        help="Test the `--automate-all` approach.",
    )
    parser.addoption(
        "--skip-confirmations",
        action="store_true",
        default=False,
        help="Skip all confirmations",
    )
    parser.addoption(
        "--platform",
        action="store",
        help="Which platform to run e2e tests for.",
        required=True,
        )


# Bundle these options into a single object.
class CLIOptions:
    def __init__(self, pkg_manager, pypi, automate_all, skip_confirmations, platform):
        self.pkg_manager = pkg_manager
        self.pypi = pypi
        self.automate_all = automate_all
        self.skip_confirmations = skip_confirmations
        self.platform = platform


@pytest.fixture(scope="session")
def cli_options(request):
    return CLIOptions(
        pkg_manager=request.config.getoption("--pkg-manager"),
        pypi=request.config.getoption("--pypi"),
        automate_all=request.config.getoption("--automate-all"),
        skip_confirmations=request.config.getoption("--skip-confirmations"),
        platform=request.config.getoption("--platform"),
    )


# --- Sample project ---


@pytest.fixture(scope="session")
def tmp_project(tmp_path_factory, pytestconfig, cli_options, request):
    """Create a copy of the local sample project, which will be deployed.

    Tests will be run against the deployed project, to make sure the deployment
      is fully functional.
    """
    # Clear cached values that may have been set.
    #   These are used in the teardown work.
    request.config.cache.set("app_name", None)
    request.config.cache.set("project_id", None)

    # Root directory of local simple_deploy project.
    sd_root_dir = Path(__file__).parent.parent.parent
    tmp_proj_dir = tmp_path_factory.mktemp("blog_project")

    print(f"\nTemp project directory: {tmp_proj_dir}")

    # Copy sample project to tmp dir, and set up the project for using simple_deploy.
    msp.setup_project(tmp_proj_dir, sd_root_dir, cli_options)

    # Store the tmp_proj_dir in the pytest cache, so we can access it in the
    #   open_test_project() plugin.
    pytestconfig.cache.set("tmp_proj_dir", str(tmp_proj_dir))

    # Return the location of the temp project.
    yield tmp_proj_dir

    # --- Cleanup ---

    # Ask if the tester wants to destroy the remote project.
    #   It's sometimes useful to keep the deployment active beyond the automated
    #   test run.
    if confirm_destroy_project(cli_options):
        # Import the platform-specific utils module and call destroy_project().
        platform = request.config.cache.get("platform", None)
        # import_path = f"tests.e2e_tests.platforms.{platform}.utils"
        import_path = f"simple_deploy.management.commands.{platform}.tests.e2e_tests.utils"
        platform_utils = importlib.import_module(import_path)
        platform_utils.destroy_project(request)
