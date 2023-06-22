import subprocess, re, os, sys, time
from pathlib import Path

import pytest


def test_dummy(tmp_project):
    """Helpful to have an empty test to run when testing setup steps."""
    pass

# Skip this test to speed up testing of setup steps.
@pytest.mark.skip
def test_platformsh_deployment(tmp_project, cli_options):

    print("\nTesting deployment to Platform.sh using the following options:")
    print(cli_options.__dict__)

    # Get the path to the Python interpreter in the virtual environment.
    #   We'll use the full path to the interpreter, rather than trying to rely on
    #   an active venv.
    if sys.platform == "win32":
        python_exe = Path(tmp_project) / "b_env" / "Scripts" / "python.exe"
    else:
        python_exe = Path(tmp_project) / "b_env" / "bin" / "python"

    # sd_command = sd_command.replace("python", python_exe.as_posix())
    python_cmd = python_exe.as_posix()

    if not cli_options.automate_all:
        print("\n\nCreating a project on Platform.sh...")
        org_output = subprocess.check_output(['platform', 'org:info'])
        org_id = re.search(r'([A-Z0-9]{26})', org_output.decode()).group(1)
        print(f"  Found Platform.sh organization id: {org_id}")
        subprocess.run(['platform', 'create', '--title', 'my_blog_project', '--org', org_id, '--region', 'us-3.platform.sh', '--yes'])

    print("Running manage.py simple_deploy...")
    if cli_options.automate_all:
        subprocess.run([python_cmd, 'manage.py', 'simple_deploy', '--platform', 'platform_sh', '--automate-all', '--integration-testing'])
    else:
        subprocess.run([python_cmd, 'manage.py', 'simple_deploy', '--platform', 'platform_sh', '--integration-testing'])

    if cli_options.pkg_manager == 'pipenv':
        subprocess.run([python_cmd, '-m', 'pipenv', 'lock'])

    if not cli_options.automate_all:
        print("\n\nCommitting changes...")
        subprocess.run(['git', 'add', '.'])
        subprocess.run(['git', 'commit', '-am', "Configured for deployment."])

        # Try pausing before making push.
        time.sleep(10)

        print("Pushing to Platform.sh...")
        subprocess.run(['platform', 'push', '--yes'])

        project_url = subprocess.check_output(['platform', 'url', '--yes']).decode().strip()
        print(f" Project URL: {project_url}")

        project_info = subprocess.check_output(['platform', 'project:info']).decode()
        project_id = re.search(r'\| id             \| ([a-z0-9]{13})', project_info).group(1)
        print(f"  Found project id: {project_id}")

    if cli_options.automate_all:
        project_info = subprocess.check_output(['platform', 'project:info']).decode()       
        project_id = re.search(r'\| id             \| ([a-z0-9]{13})', project_info).group(1)
        print(f"  Found project id: {project_id}")

        project_url = subprocess.check_output(['platform', 'url', '--yes']).decode().strip()
        print(f" Project URL: {project_url}")

    # Try pausing before testing functionality.
    time.sleep(10)
    print("\n  Testing functionality of deployed app...")
    subprocess.run([python_cmd, 'test_deployed_app_functionality.py', '--url', project_url])

    print("\n  Testing local functionality with runserver...")
    subprocess.run([python_cmd, 'manage.py', 'migrate'])
    subprocess.Popen([python_cmd, 'manage.py', 'runserver', '8008'])
    time.sleep(1)
    subprocess.run([python_cmd, 'test_deployed_app_functionality.py', '--url', "http://localhost:8008/"])
    subprocess.run(['pkill', '-f', "runserver 8008"])
    print("    Finished testing local functionality.")

    if cli_options.pypi:
        print("\n --- Finished testing latest release from PyPI. ---")
    else:
        print("\n--- Finished testing local development version. ---")

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
        subprocess.run(['platform', 'project:delete', '--project', project_id, '--yes'])
