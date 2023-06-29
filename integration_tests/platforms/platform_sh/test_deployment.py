import re, time

import pytest

from ...utils import it_helper_functions as it_utils
from ...utils.it_helper_functions import make_sp_call


# --- Platform-specific helper functions ---

def create_platformsh_project():
    """Create a project on Platform.sh."""
    print("\n\nCreating a project on Platform.sh...")
    org_output = make_sp_call("platform org:info", capture_output=True).stdout.decode()
    org_id = re.search(r'([A-Z0-9]{26})', org_output).group(1)
    print(f"  Found Platform.sh organization id: {org_id}")
    make_sp_call(f"platform create --title my_blog_project --org {org_id} --region us-3.platform.sh --yes")

def commit_configuration_changes():
    """Commit configuration changes made by simple_deploy."""
    print("\n\nCommitting changes...")
    make_sp_call("git add .")
    make_sp_call("git commit -am 'Configured for deployment.'")

def push_project():
    """Push a non-automated deployment."""
    # Try pausing before making push.
    time.sleep(30)

    print("Pushing to Platform.sh...")
    make_sp_call("platform push --yes")

    project_url = make_sp_call("platform url --yes", capture_output=True).stdout.decode().strip()
    print(f" Project URL: {project_url}")

    project_info = make_sp_call("platform project:info", capture_output=True).stdout.decode()
    project_id = re.search(r'\| id             \| ([a-z0-9]{13})', project_info).group(1)
    print(f"  Found project id: {project_id}")

    return project_url, project_id

def get_project_url_id():
    """Get project URL and id of a deployed project."""
    project_info = make_sp_call("platform project:info", capture_output=True).stdout.decode()
    project_id = re.search(r'\| id             \| ([a-z0-9]{13})', project_info).group(1)
    print(f"  Found project id: {project_id}")

    project_url = make_sp_call("platform url --yes", capture_output=True).stdout.decode().strip()
    print(f" Project URL: {project_url}")

    return project_url, project_id


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
        create_platformsh_project()

    # Run simple_deploy against the test project.
    it_utils.run_simple_deploy(python_cmd, 'platform_sh', cli_options.automate_all)

    # If testing Pipenv, lock after adding new packages.
    if cli_options.pkg_manager == 'pipenv':
        make_sp_call(f"{python_cmd} -m pipenv lock")

    # Get the deployed project's URL, and ID so we can destroy it later.
    #   This also commits configuration changes and pushes the project
    #   when testing the configuration-only workflow.
    if cli_options.automate_all:
        project_url, project_id = get_project_url_id()
    else:
        commit_configuration_changes()
        project_url, project_id = push_project()

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
        make_sp_call(f"platform project:delete --project {project_id} --yes")
