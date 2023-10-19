import re, time

import pytest

from ...utils import it_helper_functions as it_utils
from . import utils as platform_utils


# --- Test functions ---

# For normal test runs, skip this test.
# When working on setup steps, skip other tests and run this one.
#   This will force the tmp_project fixture to run, without doing a full deployment.
@pytest.mark.skip
def test_dummy(tmp_project):
    """Helpful to have an empty test to run when testing setup steps."""
    pass

# Skip this test and enable test_dummy() to speed up testing of setup steps.
# @pytest.mark.skip
def test_platformsh_deployment(tmp_project, cli_options, request):
    """Test the full, live deployment process to Platform.sh."""

    # Cache the platform name for teardown work.
    request.config.cache.set("platform", "platform_sh")

    print("\nTesting deployment to Platform.sh using the following options:")
    print(cli_options.__dict__)

    python_cmd = it_utils.get_python_exe(tmp_project)

    # Create a new project on the remote host, if not testing --automate-all.
    if not cli_options.automate_all:
        platform_utils.create_project()

    # Run simple_deploy against the test project.
    it_utils.run_simple_deploy(python_cmd, 'platform_sh', cli_options.automate_all)

    # If testing Pipenv, lock after adding new packages.
    if cli_options.pkg_manager == 'pipenv':
        it_utils.make_sp_call(f"{python_cmd} -m pipenv lock")

    # Get the deployed project's URL, and ID so we can destroy it later.
    #   This also commits configuration changes and pushes the project
    #   when testing the configuration-only workflow.
    if cli_options.automate_all:
        project_url, project_id = platform_utils.get_project_url_id()
    else:
        it_utils.commit_configuration_changes()
        project_url, project_id = platform_utils.push_project()

    # Cache project_id for teardown work.
    request.config.cache.set("project_id", project_id)

    # Test functionality of both deployed app, and local project.
    #   We want to make sure the deployment works, but also make sure we haven't
    #   affected functionality of the local project using the development server.
    remote_functionality_passed = it_utils.check_deployed_app_functionality(python_cmd, project_url)
    local_functionality_passed = it_utils.check_local_app_functionality(python_cmd)
    it_utils.summarize_results(remote_functionality_passed, local_functionality_passed,
            cli_options)

    # Make final assertions, so pytest results are meaningful.
    assert remote_functionality_passed
    assert local_functionality_passed