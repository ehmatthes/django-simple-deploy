"""Configuration for integration tests."""

import sys

import pytest


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
        "--dep-man-approach",
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
        default=True,
        help="Skip all confirmations"
    )

# Bundle these options into a single object.
class CLIOption:
    def __init__(self, dep_man_approach, pypi, automate_all, skip_confirmations):
        self.dep_man_approach = dep_man_approach
        self.pypi = pypi
        self.automate_all = automate_all
        self.skip_confirmations = skip_confirmations

@pytest.fixture(scope='session')
def cli_option(request):
    return CLIOption(
        dep_man_approach=request.config.getoption("--dep-man-approach"),
        pypi=request.config.getoption("--pypi"),
        automate_all=request.config.getoption("--automate-all"),
        skip_confirmations=request.config.getoption("--skip-confirmations")
    )