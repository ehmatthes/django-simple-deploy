import subprocess, re, os, sys, time
from pathlib import Path
from textwrap import dedent

import pytest

from ...utils.it_helper_functions import make_sp_call


# --- Platform-agnostic elper functions ---

def get_python_exe(tmp_project):
    """Get the path to the Python interpreter in the virtual environment.
    
    We'll use the full path to the interpreter, rather than trying to rely on
    an active venv.
    """
    if sys.platform == "win32":
        python_exe = Path(tmp_project) / "b_env" / "Scripts" / "python.exe"
    else:
        python_exe = Path(tmp_project) / "b_env" / "bin" / "python"

    return python_exe.as_posix()

def run_simple_deploy(python_cmd, platform, automate_all):
    """Run simple_deploy against the test project."""
    print("Running manage.py simple_deploy...")
    if automate_all:
        make_sp_call(f"{python_cmd} manage.py simple_deploy --platform {platform} --automate-all --integration-testing")
    else:
        make_sp_call(f"{python_cmd} manage.py simple_deploy --platform {platform} --integration-testing")

def check_deployed_app_functionality(python_cmd, url):
    """Test functionality of the deployed app.
    Note: Can't call this function test_ because pytest will try to run it directly.
    """
    # Pause before testing functionality, otherwise app may not yet be available.
    time.sleep(10)

    print("\n  Testing functionality of deployed app...")

    test_output = make_sp_call(f"{python_cmd} test_deployed_app_functionality.py --url {url}",
            capture_output=True).stdout.decode()

    print("    Finished testing functionality of deployed project.")

    return "--- All tested functionality works. ---" in test_output

def check_local_app_functionality(python_cmd):
    """Verify that local project still functions.
    Note: Can't call this function test_ because pytest will try to run it directly."""
    print("\n  Testing local functionality with runserver...")
    make_sp_call(f"{python_cmd} manage.py migrate")
    
    run_server = subprocess.Popen(f"{python_cmd} manage.py runserver 8008", shell=True)
    time.sleep(1)

    test_output = make_sp_call(f"{python_cmd} test_deployed_app_functionality.py --url http://localhost:8008/",
            capture_output=True).stdout.decode()
    run_server.terminate()

    print("    Finished testing local functionality.")

    return "--- All tested functionality works. ---" in test_output

def summarize_results(remote_functionality_passed, local_functionality_passed,
        cli_options):
    """Summarize test results.
    pytest's summary is not particularly helpful here.
    """
    
    if remote_functionality_passed:
        msg_remote = dedent("The deployment was successful.")
    else:
        msg_remote = dedent("""Some or all of the remote functionality tests failed.
            
            You may want to refresh the browser page, and see if
              the deployment just took longer than usual.
        """)

    if local_functionality_passed:
        msg_local = dedent("The project still works locally.")
    else:
        msg_local = dedent("The deployment process has impacted local functionality.")

    msg = dedent(f"""
        ************************************
        ***** Integration test summary *****

        Test options:
        - Tested {'PyPI' if cli_options.pypi else 'local'} version of django-simple-deploy.
        - Package manager: {cli_options.pkg_manager}
        - {'Used' if cli_options.automate_all else 'Did not use'} `--automate-all` flag.

        {msg_remote}
        {msg_local}

        *****     End test summary     *****
        ************************************

    """)
    print(msg)


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

    python_cmd = get_python_exe(tmp_project)

    # Create a new project on the remote host, if not testing --automate-all.
    if not cli_options.automate_all:
        create_platformsh_project()

    # Run simple_deploy against the test project.
    run_simple_deploy(python_cmd, 'platform_sh', cli_options.automate_all)

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
    remote_functionality_passed = check_deployed_app_functionality(python_cmd, project_url)
    local_functionality_passed = check_local_app_functionality(python_cmd)

    summarize_results(remote_functionality_passed, local_functionality_passed,
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

