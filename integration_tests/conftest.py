"""Configuration for integration tests."""

import sys
from pathlib import Path

import pytest

from .utils import manage_sample_project as msp


# --- Validity check ---

def check_valid_call():
    """Make sure the test call works for integration tests."""
    # Require -s flag.
    # This is required for some prompts. Also, integration testing involves a full
    #   deployment, and there's information generated that really needs to be in
    #   the test output at this point.
    if '-s' not in sys.argv:
        msg = "You must use the `-s` flag when running integration tests."
        print(msg)
        return False

    # Verify that a specific platform has been requested.
    if any(platform in ' '.join(sys.argv) for platform in ['platform_sh', 'fly_io', 'heroku']):
        return True
    else:
        msg = "For integration testing, you must target a specific platform."
        print(msg)
        return False

    # Can't verify it was a valid call, so return False.
    return False

if not check_valid_call():
    print("That is not a valid command for integration testing.")
    sys.exit()


# --- CLI args ---

def pytest_addoption(parser):
    parser.addoption(
        "--pkg-manager",
        action="store",
        default="req_txt",
        help="Approach for dependency management: defaults to 'req_txt'"
    )
    parser.addoption(
        "--pypi",
        action="store_true",
        default=False,
        help="Test the PyPI version of simple_deploy."
    )
    parser.addoption(
        "--automate-all",
        action="store_true",
        default=False,
        help="Test the `--automate-all` approach."
    )
    parser.addoption(
        "--skip-confirmations",
        action="store_true",
        default=False,
        help="Skip all confirmations"
    )

# Bundle these options into a single object.
class CLIOption:
    def __init__(self, pkg_manager, pypi, automate_all, skip_confirmations):
        self.pkg_manager = pkg_manager
        self.pypi = pypi
        self.automate_all = automate_all
        self.skip_confirmations = skip_confirmations

@pytest.fixture(scope='session')
def cli_options(request):
    return CLIOption(
        pkg_manager=request.config.getoption("--pkg-manager"),
        pypi=request.config.getoption("--pypi"),
        automate_all=request.config.getoption("--automate-all"),
        skip_confirmations=request.config.getoption("--skip-confirmations")
    )

# --- Sample project ---

@pytest.fixture(scope='session')
def tmp_project(tmp_path_factory, pytestconfig, cli_options):
    """Create a copy of the local sample project, which will be deployed.

    Tests will be run against the deployed project, to make sure the deployment
      is fully functional.
    """

    # Root directory of local simple_deploy project.
    sd_root_dir = Path(__file__).parent.parent
    tmp_proj_dir = tmp_path_factory.mktemp('blog_project')

    print(f"\nTemp project directory: {tmp_proj_dir}")
    
    # Copy sample project to tmp dir, and set up the project for using simple_deploy.
    msp.setup_project(tmp_proj_dir, sd_root_dir)

    # Configure the project for the appropriate dependency management system.
    msp.reset_test_project(tmp_proj_dir, cli_options)

    # Store the tmp_proj_dir in the pytest cache, so we can access it in the
    #   open_test_project() plugin.
    pytestconfig.cache.set("tmp_proj_dir", str(tmp_proj_dir))

    # Return the location of the temp project.
    return tmp_proj_dir