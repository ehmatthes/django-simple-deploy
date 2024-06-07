import re, time

import pytest

from tests.e2e_tests.utils import it_helper_functions as it_utils
from . import utils as platform_utils

from tests.e2e_tests.conftest import tmp_project, cli_options


# --- Test functions ---

# For normal test runs, skip this test.
# When working on setup steps, skip other tests and run this one.
#   This will force the tmp_project fixture to run, without doing a full deployment.
@pytest.mark.skip
def test_dummy(tmp_project, request):
    """Helpful to have an empty test to run when testing setup steps."""
    pass


# Skip this test and enable test_dummy() to speed up testing of setup steps.
# @pytest.mark.skip
def test_deployment(tmp_project, cli_options, request):
    """Test the full, live deployment process to Heroku."""

    # Cache the platform name for teardown work.
    request.config.cache.set("platform", "heroku")

    print("\nTesting deployment to Heroku using the following options:")
    print(cli_options.__dict__)

    python_cmd = it_utils.get_python_exe(tmp_project)

    # Create a new project on the remote host, if not testing --automate-all.
    if not cli_options.automate_all:
        platform_utils.create_project()

    # Run simple_deploy against the test project.
    it_utils.run_simple_deploy(python_cmd, "heroku", cli_options.automate_all)

    # If testing Pipenv, lock after adding new packages.
    if cli_options.pkg_manager == "pipenv":
        it_utils.make_sp_call(f"{python_cmd} -m pipenv lock")

    # Push the project if not using --automate-all.
    if not cli_options.automate_all:
        it_utils.commit_configuration_changes()
        platform_utils.push_project()

    # Get the deployed project's URL for testing, and get the app_name
    #   for teardown work.
    project_url, app_name = platform_utils.get_project_url_name()
    request.config.cache.set("app_name", app_name)

    # Test functionality of both deployed app, and local project.
    #   We want to make sure the deployment works, but also make sure we haven't
    #   affected functionality of the local project using the development server.
    remote_functionality_passed = it_utils.check_deployed_app_functionality(
        python_cmd, project_url
    )
    local_functionality_passed = it_utils.check_local_app_functionality(python_cmd)
    it_utils.summarize_results(
        remote_functionality_passed,
        local_functionality_passed,
        cli_options,
        tmp_project,
    )

    # Make final assertions, so pytest results are meaningful.
    assert remote_functionality_passed
    assert local_functionality_passed
