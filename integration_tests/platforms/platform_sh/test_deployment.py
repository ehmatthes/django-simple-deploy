import re, time

import pytest

from ...utils import it_helper_functions as it_utils
from . import platformsh_helper_functions as platformsh_utils


# --- Test functions ---

def test_dummy(tmp_project):
    """Helpful to have an empty test to run when testing setup steps."""
    pass

# Skip this test to speed up testing of setup steps.
# @pytest.mark.skip
def test_platformsh_deployment(tmp_project, cli_options):
    """Test the full, live deployment process to Platform.sh."""

    print("\nTesting deployment to Platform.sh using the following options:")
    print(cli_options.__dict__)

    python_cmd = it_utils.get_python_exe(tmp_project)

    # Create a new project on the remote host, if not testing --automate-all.
    if not cli_options.automate_all:
        platformsh_utils.create_platformsh_project()

    # Run simple_deploy against the test project.
    it_utils.run_simple_deploy(python_cmd, 'platform_sh', cli_options.automate_all)

    # If testing Pipenv, lock after adding new packages.
    if cli_options.pkg_manager == 'pipenv':
        it_utils.make_sp_call(f"{python_cmd} -m pipenv lock")

    # Get the deployed project's URL, and ID so we can destroy it later.
    #   This also commits configuration changes and pushes the project
    #   when testing the configuration-only workflow.
    if cli_options.automate_all:
        project_url, project_id = platformsh_utils.get_project_url_id()
    else:
        platformsh_utils.commit_configuration_changes()
        project_url, project_id = platformsh_utils.push_project()

    # Test functionality of both deployed app, and local project.
    #   We want to make sure the deployment works, but also make sure we haven't
    #   affected functionality of the local project using the development server.
    remote_functionality_passed = it_utils.check_deployed_app_functionality(python_cmd, project_url)
    local_functionality_passed = it_utils.check_local_app_functionality(python_cmd)

    it_utils.summarize_results(remote_functionality_passed, local_functionality_passed,
            cli_options)

    # Offer to destroy project.
    if not cli_options.skip_confirmations:
        while True:
            yn = input("Destroy remote project? ")
            if yn.lower() in ['y', 'yes']:
                print("Okay, tearing down...")
                tear_down = True
                break
            elif yn.lower() in ['n', 'no']:
                print("Okay, leaving project deployed.")
                tear_down = False
                break
            else:
                print("Please answer yes or no.")
    else:
        tear_down = True

    if tear_down:
        print("\nCleaning up:")
        print("  Destroying Platform.sh project...")
        it_utils.make_sp_call(f"platform project:delete --project {project_id} --yes")
