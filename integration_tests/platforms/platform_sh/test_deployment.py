import subprocess, re, os, sys, time
from pathlib import Path
from textwrap import dedent

import pytest

from ...utils.it_helper_functions import make_sp_call


def test_dummy(tmp_project):
    """Helpful to have an empty test to run when testing setup steps."""
    pass

# Skip this test to speed up testing of setup steps.
# @pytest.mark.skip
def test_platformsh_deployment(tmp_project, cli_options):
    """Test the full, live deployment process to Platform.sh."""
    print("\nTesting deployment to Platform.sh using the following options:")
    print(cli_options.__dict__)

    # Get the path to the Python interpreter in the virtual environment.
    #   We'll use the full path to the interpreter, rather than trying to rely on
    #   an active venv.
    if sys.platform == "win32":
        python_exe = Path(tmp_project) / "b_env" / "Scripts" / "python.exe"
    else:
        python_exe = Path(tmp_project) / "b_env" / "bin" / "python"
    python_cmd = python_exe.as_posix()

    if not cli_options.automate_all:
        print("\n\nCreating a project on Platform.sh...")
        org_output = make_sp_call("platform org:info", capture_output=True).stdout.decode()
        org_id = re.search(r'([A-Z0-9]{26})', org_output).group(1)
        print(f"  Found Platform.sh organization id: {org_id}")
        make_sp_call(f"platform create --title my_blog_project --org {org_id} --region us-3.platform.sh --yes")

    print("Running manage.py simple_deploy...")
    if cli_options.automate_all:
        make_sp_call(f"{python_cmd} manage.py simple_deploy --platform platform_sh --automate-all --integration-testing")
    else:
        make_sp_call(f"{python_cmd} manage.py simple_deploy --platform platform_sh --integration-testing")

    if cli_options.pkg_manager == 'pipenv':
        make_sp_call(f"{python_cmd} -m pipenv lock")

    if not cli_options.automate_all:
        print("\n\nCommitting changes...")
        make_sp_call("git add .")
        make_sp_call("git commit -am 'Configured for deployment.'")

        # Try pausing before making push.
        time.sleep(30)

        print("Pushing to Platform.sh...")
        make_sp_call("platform push --yes")

        project_url = make_sp_call("platform url --yes", capture_output=True).stdout.decode().strip()
        print(f" Project URL: {project_url}")

        project_info = make_sp_call("platform project:info", capture_output=True).stdout.decode()
        project_id = re.search(r'\| id             \| ([a-z0-9]{13})', project_info).group(1)
        print(f"  Found project id: {project_id}")

    if cli_options.automate_all:
        project_info = make_sp_call("platform project:info", capture_output=True).stdout.decode()
        project_id = re.search(r'\| id             \| ([a-z0-9]{13})', project_info).group(1)
        print(f"  Found project id: {project_id}")

        project_url = make_sp_call("platform url --yes", capture_output=True).stdout.decode().strip()
        print(f" Project URL: {project_url}")

    # Try pausing before testing functionality.
    time.sleep(10)
    print("\n  Testing functionality of deployed app...")

    test_output = make_sp_call(f"{python_cmd} test_deployed_app_functionality.py --url {project_url}",
            capture_output=True).stdout.decode()

    if "--- All tested functionality works. ---" in test_output:
        remote_functionality_passed = True
    else:
        remote_functionality_passed = False

    print("\n  Testing local functionality with runserver...")
    make_sp_call(f"{python_cmd} manage.py migrate")
    
    run_server = subprocess.Popen(f"{python_cmd} manage.py runserver 8008", shell=True)
    time.sleep(1)
    test_output = make_sp_call(f"{python_cmd} test_deployed_app_functionality.py --url http://localhost:8008/",
            capture_output=True).stdout.decode()
    run_server.terminate()

    if "--- All tested functionality works. ---" in test_output:
        local_functionality_passed = True
    else:
        local_functionality_passed = False

    print("    Finished testing local functionality.")

    if cli_options.pypi:
        print("\n --- Finished testing latest release from PyPI. ---")
    else:
        print("\n--- Finished testing local development version. ---")

    # Summarize test results.
    #   pytest's summary is not particularly helpful here.
    if remote_functionality_passed:
        msg_remote = dedent("The deployment was successful.")
    else:
        msg_remote = dedent("""
            Some or all of the remote functionality tests failed.
            
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

        {msg_remote}

        {msg_local}
        
        *****     End test summary     *****
        ************************************

    """)
    print(msg)

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

