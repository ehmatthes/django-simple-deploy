import os
import subprocess
import sys
from pathlib import Path
from shutil import copytree
from shlex import split

def setup_project(tmp_proj_dir, sd_root_dir):
    """Set up the test project.
    - Copy the sample project to a temp dir.
    - Set up a venv.
    - Install requiremenst for the sample project.
    - Install the local, editable version of simple_deploy.
    - Make an initial commit.
    - Add simple_deploy to INSTALLED_APPS.
    """

    # Copy sample project to temp dir.
    sample_project_dir = sd_root_dir / "sample_project/blog_project"
    copytree(sample_project_dir, tmp_proj_dir, dirs_exist_ok=True)

    # Create a virtual envronment. Set the path to the environemnt, instead of
    #   activating it. It's easier to use the venv directly than to activate it,
    #   with all these separate subprocess.run() calls.
    venv_dir = tmp_proj_dir / "b_env"
    subprocess.run([sys.executable, "-m", "venv", venv_dir])

    # Install requirements for sample project, from vendor/.
    #   Don't upgrade pip, as that would involve a network call. When troubleshooting,
    #   keep in mind someone at some point might just need to upgrade their pip.
    pip_path = venv_dir / ("Scripts" if os.name == "nt" else "bin") / "pip"
    requirements_path = tmp_proj_dir / "requirements.txt"
    subprocess.run([pip_path, "install", "--no-index", "--find-links", sd_root_dir / "vendor", "-r", requirements_path])

    # Install the local version of simple_deploy (the version we're testing).
    # Note: We don't need an editable install, but a non-editable install is *much* slower.
    #   We may be able to use --cache-dir to address this, but -e is working fine right now.
    subprocess.run([pip_path, "install", "-e", sd_root_dir])

    # Make an initial git commit, so we can reset the project every time we want
    #   to test a different simple_deploy command. This is much more efficient than
    #   tearing down the whole sample project and rebuilding it from scratch.
    # We use a git tag to do the reset, instead of trying to capture the initial hash.
    git_exe = "git"
    os.chdir(tmp_proj_dir)
    subprocess.run([git_exe, "init"])
    subprocess.run([git_exe, "branch", "-m", "main"])
    subprocess.run([git_exe, "add", "."])
    subprocess.run([git_exe, "commit", "-am", "Initial commit."])
    subprocess.run([git_exe, "tag", "-am", "", "INITIAL_STATE"])

    # Add simple_deploy to INSTALLED_APPS.
    settings_file_path = tmp_proj_dir / "blog/settings.py"
    settings_content = settings_file_path.read_text()
    new_settings_content = settings_content.replace("# Third party apps.", "# Third party apps.\n    'simple_deploy',")
    settings_file_path.write_text(new_settings_content)


def call_simple_deploy(tmp_dir, invalid_sd_command):
    # Change to the temp dir
    os.chdir(tmp_dir)

    # print(f"tmp_dir: {tmp_dir}")

    # # Activate existing virtual environment
    # venv_activate = Path(tmp_dir) / "b_env" / "bin" / "activate"
    # activate_command = f"source {venv_activate}"
    # source_env = subprocess.Popen(activate_command, stdout=subprocess.PIPE, shell=True, executable="/bin/zsh")
    # source_env.communicate()

    # Add --unit-testing argument to call
    invalid_sd_command = invalid_sd_command.replace("simple_deploy", "simple_deploy --unit-testing")

    # Get the path to the Python interpreter in the virtual environment
    python_exe = Path(tmp_dir) / "b_env" / "bin" / "python"
    # Replace 'python' with the path to the virtual environment's Python interpreter
    invalid_sd_command = invalid_sd_command.replace("python", str(python_exe))

    # Make invalid call
    invalid_call = subprocess.Popen(split(invalid_sd_command), stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    stdout, stderr = invalid_call.communicate()
    # assert not stdout
    # assert not stderr



    # Make invalid call
    # print('--- HERE ---', file=sys.stderr)
    # sys.stderr.write('=== HERE ===')
    # print(invalid_sd_command, end='')
    # invalid_call = subprocess.Popen(split(invalid_sd_command), stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    # stdout, stderr = invalid_call.communicate()

    return stdout, stderr
