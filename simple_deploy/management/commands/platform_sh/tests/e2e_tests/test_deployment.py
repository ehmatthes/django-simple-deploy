import re, time, os

import pytest

from tests.e2e_tests.utils import it_helper_functions as it_utils
from . import utils as platform_utils

from tests.e2e_tests.conftest import tmp_project, cli_options


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
def test_deployment(tmp_project, cli_options, request):
    """Test the full, live deployment process to Platform.sh.

    Note: On Windows, this must be run from a bash terminal, such as Git Bash,
        or through WSL.
      On Windows you may see a popup about authenticating an RSA key fingerprint. Sometimes this
        is hidden by a console window. Look for that confirmation if a platform command
        hangs. Enter 'yes' (not just 'y') into that box if it appears. It obscures what
        you type with asterisks, but it's just looking for 'yes'.
      Confirming the RSA key in the popup generates a `.ssh/known_hosts` file, which then allows
        you to use non-bash shells. That behavior is *really* confusing, though. I don't think the
        platform.sh CLI was designed to be used on native Windows at all. :/
      Also, sometimes helps to run `platform auth:logout` followed by `platform auth:browser-login`.
    """

    # Cache the platform name for teardown work.
    request.config.cache.set("platform", "platform_sh")

    print("\nTesting deployment to Platform.sh using the following options:")
    print(cli_options.__dict__)

    platform_utils.check_logged_in()

    python_cmd = it_utils.get_python_exe(tmp_project)

    # Create a new project on the remote host, if not testing --automate-all.
    if not cli_options.automate_all:
        platform_utils.create_project()

        # `platform create` creates `.platform/local`. This is ignored on macOS,
        #   but not on Windows. There's a `.platform/local/.gitignore` file with a
        #   single forward slash in it. Does this ignore that directory on macOS,
        #   but not on Windows? Committing here, so we got into running sd with a
        #   clean `git status`.
        if os.name == "nt":
            it_utils.make_sp_call("git add .")
            it_utils.make_sp_call("git commit -am 'Created platform_sh project.'")

    # Run simple_deploy against the test project.
    it_utils.run_simple_deploy(python_cmd, "platform_sh", cli_options.automate_all)

    # If testing Pipenv, lock after adding new packages.
    if cli_options.pkg_manager == "pipenv":
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
