"""Helper functions specific to Heroku."""

import re, time

from tests.e2e_tests.utils.it_helper_functions import make_sp_call


def create_project():
    """Create a project on Heroku."""
    print("\n\nCreating a project on Heroku...")
    make_sp_call("heroku create")


def push_project():
    """Make a non-automated deployment."""
    # Consider pausing before the deployment. Some platforms need a moment
    #   for the newly-created resources to become fully available.
    # time.sleep(30)

    print("Deploying to Heroku...")
    make_sp_call("git push heroku main")

    print("  Migrating deployed project...")
    make_sp_call("heroku run python manage.py migrate")

    print("  Opening project...")
    make_sp_call("heroku open")


def get_project_url_name():
    """Get project URL and app name of the deployed project."""
    output = (
        make_sp_call("heroku apps:info", capture_output=True).stdout.decode().strip()
    )

    re_app_name = r"=== (.*)"
    app_name = re.search(re_app_name, output).group(1).strip()

    print(f"  Found app name: {app_name}")

    # Get URL.
    re_url = r"Web URL:.*(https:.*)"
    project_url = re.search(re_url, output).group(1).strip()
    print(f"  Project URL: {project_url}")

    return project_url, app_name


def destroy_project(request):
    """Destroy the deployed project, and all remote resources."""
    print("\nCleaning up:")

    app_name = request.config.cache.get("app_name", None)
    if not app_name:
        print("  No app name found; can't destroy any remote resources.")
        return None

    print("  Destroying Heroku project...")
    make_sp_call(f"heroku apps:destroy --app {app_name} --confirm {app_name}")
