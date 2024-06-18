"""Helper functions specific to Platform.sh."""

import re, time

import pytest

from tests.e2e_tests.utils.it_helper_functions import make_sp_call


def check_logged_in():
    """Check that user is currently logged in to Platform.sh through CLI."""
    print("\nVerifying logged in to Platform.sh CLI...")
    auth_info_output = make_sp_call("platform auth:info --quiet", capture_output=True)
    if "LoginRequiredException" in auth_info_output.stderr.decode():
        msg = "\n----- Error: Not logged in through CLI -----"
        msg += "\nPlease log in to the Platform.sh CLI and then run the e2e test."
        msg += "\n  You can log in with the command: platform login"
        msg += "\n-----\n"
        print(msg)

        exit_msg = "Please run `platform login` and then run e2e tests."
        pytest.exit(exit_msg)


def create_project():
    """Create a project on Platform.sh."""
    print("\n\nCreating a project on Platform.sh...")
    org_output = make_sp_call("platform org:info", capture_output=True).stdout.decode()
    org_id = re.search(r"([A-Z0-9]{26})", org_output).group(1)
    print(f"  Found Platform.sh organization id: {org_id}")
    make_sp_call(
        f"platform create --title my_blog_project --org {org_id} --region us-3.platform.sh --yes"
    )


def push_project():
    """Push a non-automated deployment."""
    # Pause before making push, otherwise project resources may not be available.
    time.sleep(30)

    print("Pushing to Platform.sh...")
    make_sp_call("platform push --yes")

    project_url = (
        make_sp_call("platform url --yes", capture_output=True).stdout.decode().strip()
    )
    print(f" Project URL: {project_url}")

    project_info = make_sp_call(
        "platform project:info", capture_output=True
    ).stdout.decode()
    project_id = re.search(r"\| id             \| ([a-z0-9]{13})", project_info).group(
        1
    )
    print(f"  Found project id: {project_id}")

    return project_url, project_id


def get_project_url_id():
    """Get project URL and id of a deployed project."""
    project_info = make_sp_call(
        "platform project:info", capture_output=True
    ).stdout.decode()
    project_id = re.search(r"\| id             \| ([a-z0-9]{13})", project_info).group(
        1
    )
    print(f"  Found project id: {project_id}")

    project_url = (
        make_sp_call("platform url --yes", capture_output=True).stdout.decode().strip()
    )
    print(f" Project URL: {project_url}")

    return project_url, project_id


def destroy_project(request):
    """Destroy the deployed project, and all remote resources."""
    print("\nCleaning up:")

    project_id = request.config.cache.get("project_id", None)
    if not project_id:
        print("  No project id found; can't destroy any remote resources.")

    print("  Destroying Platform.sh project...")
    make_sp_call(f"platform project:delete --project {project_id} --yes")
