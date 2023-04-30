import subprocess, re
from pathlib import Path
from time import sleep

import pytest

from .utils import manage_sample_project as msp
from .utils import ut_helper_functions as uhf


# Check prerequisites before running unit tests.
@pytest.fixture(scope='session', autouse=True)
def check_prerequisites():
    """Make sure dev environment supports unit tests."""
    uhf.check_package_manager_available('poetry')
    uhf.check_package_manager_available('pipenv')


@pytest.fixture(scope='session')
def tmp_project(tmp_path_factory):
    """Create a copy of the local sample project, so that platform-specific modules
    can call simple_deploy.

    Most tests will examine how the project was modified.
    """

    # Pause, or the tmpdir won't be usable.
    sleep(0.2)

    # Root directory of local simple_deploy project.
    sd_root_dir = Path(__file__).parent.parent
    tmp_proj_dir = tmp_path_factory.mktemp('blog_project')

    # To see where pytest creates the tmp_proj_dir, uncomment the following line.
    #   All tests will fail, but the AssertionError will show you the full path
    #   to tmp_proj_dir.
    # assert not tmp_proj_dir
    
    # Copy sample project to tmp dir, and set up the project for using simple_deploy.
    msp.setup_project(tmp_proj_dir, sd_root_dir)

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
    This auto-runs for all test modules in the /unit_tests/platforms/ directory.
    """

    # Identify the platform that's being tested. We're looking for the element
    #   in the test module path immediately after /unit_tests/platforms/.
    re_platform = r".*/unit_tests/platforms/(.*?)/.*"
    test_module_path = request.path
    m = re.match(re_platform, str(test_module_path))

    if m:
        platform = m.group(1)
    else:
        # The currently running test module is not in /unit_tests/platforms/, so it
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
