import os
import subprocess
import sys
from pathlib import Path
from shutil import copytree
from shlex import split

def setup_project(tmp_proj_dir, sd_root_dir):
    sample_project_dir = sd_root_dir / "sample_project/blog_project"
    copytree(sample_project_dir, tmp_proj_dir, dirs_exist_ok=True)

    venv_dir = tmp_proj_dir / "b_env"
    subprocess.run([sys.executable, "-m", "venv", venv_dir])

    pip_path = venv_dir / ("Scripts" if os.name == "nt" else "bin") / "pip"
    requirements_path = tmp_proj_dir / "requirements.txt"
    subprocess.run([pip_path, "install", "--no-index", "--find-links", sd_root_dir / "vendor", "-r", requirements_path])



    # HERE. 
    # This is the line that causes lots of errors.
    # Interrupting before this line means simple deploy is not available in the test project.
    # There is no stderr output when stopping here.
    subprocess.run([pip_path, "install", "--upgrade", "pip"])
    subprocess.run([pip_path, "install", "-e", sd_root_dir])
    # assert False

    # sd_root_dir: PosixPath('/Users/eric/projects/django-simple-deploy')
    # Try going into the test project directory before and after this line is run,
    #   and see if simple_deploy is installed, and runs --help.

    # HERE.
    

    subprocess.run([pip_path, "freeze"], stdout=open(tmp_proj_dir / "installed_packages.txt", "w"))

    git_exe = "git"
    os.chdir(tmp_proj_dir)
    subprocess.run([git_exe, "init"])
    subprocess.run([git_exe, "branch", "-m", "main"])
    subprocess.run([git_exe, "add", "."])
    subprocess.run([git_exe, "commit", "-am", "Initial commit."])
    subprocess.run([git_exe, "tag", "-am", "", "INITIAL_STATE"])

    settings_file_path = tmp_proj_dir / "blog/settings.py"
    with open(settings_file_path, "r") as f:
        settings_content = f.read()

    new_content = settings_content.replace("# Third party apps.", "# Third party apps.\n    'simple_deploy',")
    with open(settings_file_path, "w") as f:
        f.write(new_content)


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
