"""Configuration for integration_tests/."""

import subprocess, re, sys, os, tempfile
from pathlib import Path
from time import sleep

import pytest

from .utils import manage_sample_project as msp
from .utils import it_helper_functions as ihf


# --- Plugins ---

# Trying to make a plugin to be able to run `pytest -x -p open-test-project`
#   See: https://github.com/ehmatthes/django-simple-deploy/issues/240
#   Currently works: `pytest -x --open-test-project`
# 
# I tried putting this in an integration_tests/plugins/ dir, but could not get it to load.
#   The only thing that worked was:
#   $ PYTHONPATH=../ pytest -x --open-test-project
# I tried setting pythonpath in pytest.ini, and integration_tests/ was added to the path,
#   but it still couldn't find the plugin.

def pytest_addoption(parser):
    parser.addoption("--open-test-project", action="store_true",
        help="Open the test project in an active terminal window at the end of the test run")

def pytest_sessionfinish(session, exitstatus):
    if session.config.getoption("--open-test-project", None):
        # DEV: How can we identify the terminal environment where
        #   pytest is currently running?

        # DEV: This should probably bail if the -x flag was not used.
        #   If there's no failing test, this is not helpful.
        #   If there is a failing test that was then reset, this is not helpful.

        # DEV: The body of this function shouldn't be in an if-block.
        #   Return early if the --open-test-project flag not set, then do work
        #   in main body block.

        # Currently, this plugin only supports macOS.
        if sys.platform != 'darwin':
            print("The --open-test-project option is not yet supported on your platform.")
            return

        tmp_proj_dir = session.config.cache.get("tmp_proj_dir", ".")

        # Write a script containing all the commands we need to set up
        #   a terminal environment for exploring the test project in its
        #   final state.
        shell_script = rf"""
        #!/bin/bash
        cd {tmp_proj_dir}
        export PS1="\W$ "
        source b_env/bin/activate
        git status
        git log --pretty=oneline
        echo "\n--- Feel free to poke around the temp test project! ---"
        bash
        """

        # Write the script to a temporary file.
        #   Don't write this in tmp_proj_dir, as that would affect git status.
        script_dir = tempfile.gettempdir()
        path = Path(f"{script_dir}/commands.sh")
        path.write_text(shell_script)

        # Make the script executable.
        os.chmod(f"{script_dir}/commands.sh", 0o755)

        # Open a new terminal and run the script
        cmd = f'open -a Terminal {script_dir}/commands.sh'
        subprocess.run(cmd.split())

# --- /Plugins ---


# Check prerequisites before running integration tests.
@pytest.fixture(scope='session', autouse=True)
def check_prerequisites():
    """Make sure dev environment supports integration tests."""
    ihf.check_package_manager_available('poetry')
    ihf.check_package_manager_available('pipenv')


@pytest.fixture(scope='session')
def tmp_project(tmp_path_factory, pytestconfig):
    """Create a copy of the local sample project, so that platform-specific modules
    can call simple_deploy.

    Most tests will examine how the project was modified.
    """

    # Pause, or the tmpdir won't be usable.
    sleep(0.2)

    # Root directory of local simple_deploy project.
    sd_root_dir = Path(__file__).parents[2]
    tmp_proj_dir = tmp_path_factory.mktemp('blog_project')

    # To see where pytest creates the tmp_proj_dir, uncomment the following line.
    #   All tests will fail, but the AssertionError will show you the full path
    #   to tmp_proj_dir.
    # assert not tmp_proj_dir
    
    # Copy sample project to tmp dir, and set up the project for using simple_deploy.
    msp.setup_project(tmp_proj_dir, sd_root_dir)

    # Store the tmp_proj_dir in the pytest cache, so we can access it in the
    #   open_test_project() plugin.
    pytestconfig.cache.set("tmp_proj_dir", str(tmp_proj_dir))

    # Return the location of the temp project.
    return tmp_proj_dir


@pytest.fixture(scope='module', params=["req_txt", "poetry", "pipenv"])
def reset_test_project(request, tmp_project):
    """Reset the test project, so it can be used again by another test module,
    which may be another platform.
    """
    msp.reset_test_project(tmp_project, request.param)

@pytest.fixture(scope='module', autouse=True)
def run_simple_deploy(reset_test_project, tmp_project, request):
    """Call simple deploy, targeting the platform that's currently being tested.
    This auto-runs for all test modules in the /integration_tests/platforms/ directory.
    """

    # Identify the platform that's being tested. We're looking for the element
    #   in the test module path immediately after /integration_tests/platforms/.
    # Note that we can use `{re.escape(os.sep)}` and avoid the if block, but it's less readable.
    if sys.platform == 'win32':
        re_platform = r".*\\management\\commands\\(.*?)\\.*"
    else:
        re_platform = r".*/management/commands/(.*?)/.*"
    test_module_path = request.path
    print("\n\ntest_module_path:", test_module_path, "\n\n")
    m = re.match(re_platform, str(test_module_path))

    if m:
        platform = m.group(1)
    else:
        # The currently running test module is not in /integration_tests/platforms/, so it
        #   doesn't need to run simple_deploy.
        return

    cmd = f"python manage.py simple_deploy"
    msp.call_simple_deploy(tmp_project, cmd, platform)


@pytest.fixture()
def pkg_manager(request):
    """Get the fixture parameter that specifies the pkg_manager in use.

    Returns:
    - String representing package manager: req_txt | poetry | pipenv
    """
    return request.node.callspec.params.get("reset_test_project")
