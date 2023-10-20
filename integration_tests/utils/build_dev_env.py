"""
Builds a copy of the sample project in a way that can be used for manual
  (and automated?) testing of django-simple-deploy.

Notes:
- This should probably be moved to developer_resources/.
- Let people specify a location where the dev project should live.
- Currently writes the project to:
  project_dir = Path.home() / f"projects/dsd-dev-project_{random_id}"
- Final output:
    --- Finished setup ---
      Your project is ready to use at: /Users/eric/projects/dsd-dev-project_zepbz
- Currently, does not run migrate.      
"""

import os, sys, subprocess, random, string, shlex, argparse
from pathlib import Path
from shutil import copy, copytree, rmtree


# --- CLI args ---

# Usage: python build_dev_env.py --pkg-manager [req_txt | poetry | pipenv] --target [development_version | pypi]

parser = argparse.ArgumentParser(description="Build development environment")

parser.add_argument('--pkg-manager', 
                    type=str, 
                    default='req_txt',
                    help='The package manager to use (e.g., "req_txt", "poetry", "pipenv")')

parser.add_argument('--target', 
                    type=str, 
                    default='development_version',
                    help='The target environment (e.g., "development_version", "pypi")')

args = parser.parse_args()

pkg_manager = args.pkg_manager
target = args.target

# --- Helper functions

def make_sp_call(cmd, capture_output=False):
    """Make a subprocess call.

    This wrapper function lets test code use full commands, rather than
      lists of command parts. This makes it much easier to follow what testing
      code is doing.

    Note: This can not be used for calls that require shell=True. Those calls
      need to be passed as a single string, not as cmd_parts.

    Returns: None, or CompletedProcess instance.
    """
    cmd_parts = shlex.split(cmd)
    return subprocess.run(cmd_parts, capture_output=capture_output)

def activate_and_run(command, project_dir):
    """Run a command that needs to be run using a venv."""
    activate_path = project_dir / ".venv" / "bin" / "activate"
    full_command = f". {activate_path} && {command}"
    subprocess.run(full_command, shell=True, check=True, cwd=project_dir)

def remove_unneeded_files(proj_dir, pkg_manager):
    """Remove dependency management files not needed for the
    selected package manager.
    """
    if pkg_manager == "req_txt":
        (proj_dir / "pyproject.toml").unlink()
        (proj_dir / "Pipfile").unlink()
    elif pkg_manager == "poetry":
        (proj_dir / "requirements.txt").unlink()
        (proj_dir / "Pipfile").unlink()
    elif pkg_manager == "pipenv":
        (proj_dir / "requirements.txt").unlink()
        (proj_dir / "pyproject.toml").unlink()

def add_simple_deploy(tmp_dir):
    """Add simple_deploy to INSTALLED_APPS in the test project."""
    settings_file_path = tmp_dir / "blog/settings.py"
    settings_content = settings_file_path.read_text()
    new_settings_content = settings_content.replace("# Third party apps.", "# Third party apps.\n    'simple_deploy',")
    settings_file_path.write_text(new_settings_content)


# --- Build development environment. ---

sd_root_dir = Path(__file__).parents[2]

random_id = ''.join(random.choices(string.ascii_letters + string.digits, k=5)).lower()
project_dir = Path.home() / f"projects/dsd-dev-project_{random_id}"

# Copy sample project to project dir.
sample_project_dir = sd_root_dir / "sample_project/blog_project"
copytree(sample_project_dir, project_dir, dirs_exist_ok=True)
remove_unneeded_files(project_dir, pkg_manager)

# Create a virtual envronment. Set the path to the environemnt, instead of
#   activating it. It's easier to use the venv directly than to activate it,
#   with all these separate subprocess.run() calls.
venv_dir = project_dir / ".venv"
make_sp_call(f"{sys.executable} -m venv {venv_dir}")

# Install requirements for sample project, from vendor/.
# Do this using the same package manager that the end user has selected.
pip_path = venv_dir / ("Scripts" if os.name == "nt" else "bin") / "pip"
vendor_path = sd_root_dir / "vendor"
activate_path = venv_dir / "bin" / "activate"

if pkg_manager == 'req_txt':
    #   Don't upgrade pip, unless it starts to cause problems.
    requirements_path = project_dir / "requirements.txt"
    cmd = f"{pip_path} install --no-index --find-links {vendor_path} -r {requirements_path}"
    make_sp_call(cmd)

elif pkg_manager == 'poetry':
    activate_and_run("poetry cache clear --all pypi -n", project_dir)
    activate_and_run("poetry install", project_dir)

elif pkg_manager == 'pipenv':
    # Install pipenv.
    cmd = f"{pip_path} install pipenv"
    make_sp_call(cmd)

    # Activate virtual environment and install dependencies with pipenv
    activate_and_run("pipenv install", project_dir)

# Usually, install the local version of simple_deploy (the version we're developing).
# Note: We don't need an editable install, but a non-editable install is *much* slower.
#   We may be able to use --cache-dir to address this, but -e is working fine right now.
# If `--pypi` flag has been passed, install from PyPI.
if pkg_manager == 'req_txt':
    if target == "pypi":
        make_sp_call("pip cache purge")
        make_sp_call(f"{pip_path} install django-simple-deploy")
    else:
        make_sp_call(f"{pip_path} install -e {sd_root_dir}")

elif pkg_manager == 'poetry':
    # Use pip to install the local version.
    # We could install the local wheel file using `poetry add`, but then 
    #   the lock file won't work on the remote server. We're really testing
    #   how simple_deploy handles a poetry environment, we're not testing
    #   how poetry installs the local package. So this should reliably test
    #   whether an end user who uses poetry is able to use simple_deploy
    #   successfully.
    if target == "pypi":
        activate_and_run("poetry add django-simple-deploy", project_dir)
    else:
        make_sp_call(f"{pip_path} install -e {sd_root_dir}")

elif pkg_manager == 'pipenv':
    if target == "pypi":
        activate_and_run("pipenv install django-simple-deploy", project_dir)
    else:
        # Install local (editable) version of django-simple-deploy.
        activate_and_run(f"pipenv install -e {sd_root_dir}", project_dir)

        # Rewrite the specification for dsd in Pipfile, so remote server
        #   won't try to install local version.
        pipfile_path = project_dir / "Pipfile"
        pipfile_lines = pipfile_path.read_text().splitlines()
        new_pipfile_lines = []
        for line in pipfile_lines:
            if "django-simple-deploy" in line:
                new_pipfile_lines.append('django-simple-deploy = "*"')
            else:
                new_pipfile_lines.append(line)

        new_pipfile_contents = "\n".join(new_pipfile_lines)
        pipfile_path.write_text(new_pipfile_contents)

        # Generate lock file.
        activate_and_run("pipenv lock", project_dir)

# Make an initial git commit, so we can reset the project every time we want
#   to run a different simple_deploy command. This is much more efficient than
#   tearing down the whole sample project and rebuilding it from scratch.
# We use a git tag to do the reset, instead of trying to capture the initial hash.
git_exe = "git"
os.chdir(project_dir)
make_sp_call("git init")
make_sp_call("git branch -m main")
make_sp_call("git add .")
make_sp_call("git commit -am 'Initial commit.'")
make_sp_call("git tag -am '' 'INITIAL_STATE'")

# Add simple_deploy to INSTALLED_APPS.
add_simple_deploy(project_dir)

# Make sure we have a clean status before calling simple_deploy.
make_sp_call("git commit -am 'Added simple_deploy to INSTALLED_APPS.'")

# Repeat the project directory, so user can go there easily.
print("\n\n --- Finished setup ---")
print(f"  Your project is ready to use at: {project_dir}")