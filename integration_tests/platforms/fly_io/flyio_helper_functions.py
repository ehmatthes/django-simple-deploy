"""Helper functions specific to Fly.io."""

import re, time

from ...utils.it_helper_functions import make_sp_call


def create_project():
    """Create a project on Fly.io."""
    print("\n\nCreating a project on Fly.io...")
    output = make_sp_call(f"fly apps create --generate-name", capture_output=True).stdout.decode().strip()
    print('create_project output:', output)

    re_app_name = r'New app created: (.*)'
    app_name = re.search(re_app_name, output).group(1)
    print(f"  App name: {app_name}")

    return app_name

def commit_configuration_changes():
    """Commit configuration changes made by simple_deploy."""
    print("\n\nCommitting changes...")
    make_sp_call("git add .")
    make_sp_call("git commit -am 'Configured for deployment.'")

def deploy_project():
    """Make a non-automated deployment."""
    # # Pause before making push, otherwise project resources may not be available.
    # time.sleep(30)

    print("Deploying to Fly.io...")
    make_sp_call("fly deploy")

    # Open project and get URL.
    output = make_sp_call("fly open", capture_output=True).stdout.decode().strip()
    print('fly open output:', output)

    re_url = r'opening (http.*) \.\.\.'
    project_url = re.search(re_url, output).group(1)
    if 'https' not in project_url:
        project_url = project_url.replace('http', 'https')

    print(f"  Project URL: {project_url}")

    return project_url

def get_project_url_name():
    """Get project URL and app name of a deployed project."""
    output = make_sp_call("fly info", capture_output=True).stdout.decode().strip()

    re_app_name = r'.*Hostname = (.*)\.fly\.dev'
    app_name = re.search(re_app_name, output).group(1)

    print(f"  Found app name: {app_name}")

    # Build URL.
    project_url = f"https://{app_name}.fly.dev"
    print(f"  Project URL: {project_url}")

    return project_url, app_name

def destroy_project(app_name):
    """Destroy the deployed project, and all remote resources."""
    print("\nCleaning up:")
    print("  Destroying Fly.io project...")
    # make_sp_call(f"fly apps destroy -y {app_name}")
    cmd = f"fly apps destroy -y {app_name}"
    print("  destroy app command:", cmd)
    make_sp_call(cmd)

    print("  Destorying Fly.io database...")
    # make_sp_call(f"fly apps destroy -y {app_name}-db")
    cmd = f"fly apps destroy -y {app_name}-db"
    print("  destroy db command:", cmd)
    make_sp_call(cmd)