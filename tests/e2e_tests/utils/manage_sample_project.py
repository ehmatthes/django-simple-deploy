import os, sys, subprocess
from pathlib import Path
from shutil import copy, copytree, rmtree

from .it_helper_functions import make_sp_call


# --- Helper functions ---

def add_simple_deploy(tmp_dir):
    """Add simple_deploy to INSTALLED_APPS in the test project."""
    settings_file_path = tmp_dir / "blog/settings.py"
    settings_content = settings_file_path.read_text()
    new_settings_content = settings_content.replace("# Third party apps.", "# Third party apps.\n    'simple_deploy',")
    settings_file_path.write_text(new_settings_content)


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


# --- Main functions

def setup_project(tmp_proj_dir, sd_root_dir, cli_options):
    """Set up the test project.
    - Copy the sample project to a temp dir.
    - Set up a venv.
    - Install requirements for the sample project.
    - Install the appropriate version of simple_deploy.
    - Make an initial commit.
    - Add simple_deploy to INSTALLED_APPS.

    Returns:
    - None
    """
    try:
        subprocess.run(["uv", "--version"])
    except FileNotFoundError:
        uv_available = False
    else:
        uv_available = True

    # Copy sample project to temp dir.
    sample_project_dir = sd_root_dir / "sample_project/blog_project"
    copytree(sample_project_dir, tmp_proj_dir, dirs_exist_ok=True)
    remove_unneeded_files(tmp_proj_dir, cli_options.pkg_manager)

    # Create a virtual envronment. Set the path to the environemnt, instead of
    #   activating it. It's easier to use the venv directly than to activate it,
    #   with all these separate subprocess.run() calls.
    venv_dir = tmp_proj_dir / "b_env"
    if uv_available:
        cmd = f"uv venv {venv_dir}"
    else:
        cmd = f"{sys.executable} -m venv {venv_dir}"
    make_sp_call(cmd)

    # Install requirements for sample project, from vendor/.
    # Do this using the same package manager that the end user has selected.
    pip_path = venv_dir / ("Scripts" if os.name == "nt" else "bin") / "pip"
    vendor_path = sd_root_dir / "vendor"
    activate_path = venv_dir / "bin" / "activate"

    if cli_options.pkg_manager == 'req_txt':
        #   Don't upgrade pip, unless it starts to cause problems.
        requirements_path = tmp_proj_dir / "requirements.txt"
        if uv_available:
            path_to_python = venv_dir / "bin" / "python"
            if sys.platform == "win32":
                path_to_python = venv_dir / "Scripts" / "python.exe"
            cmd = f"uv pip install --python {path_to_python} --find-links {vendor_path} -r {requirements_path}"
        else:
            cmd = f"{pip_path} install --no-index --find-links {vendor_path} -r {requirements_path}"
        make_sp_call(cmd)

    elif cli_options.pkg_manager == 'poetry':
        cmd = f"cd {tmp_proj_dir} && . {activate_path} && poetry cache clear --all pypi -n"
        subprocess.run(cmd, shell=True, check=True)

        cmd = f"cd {tmp_proj_dir} && . {activate_path} && poetry install"
        subprocess.run(cmd, shell=True, check=True)

    elif cli_options.pkg_manager == 'pipenv':
        # Install pipenv.
        cmd = f"cd {tmp_proj_dir} && {pip_path} install pipenv"
        subprocess.run(cmd, shell=True, check=True)

        cmd = f"cd {tmp_proj_dir} && . {activate_path} && pipenv install"# --skip-lock"
        subprocess.run(cmd, shell=True, check=True)

    # Usually, install the local version of simple_deploy (the version we're testing).
    # Note: We don't need an editable install, but a non-editable install is *much* slower.
    #   We may be able to use --cache-dir to address this, but -e is working fine right now.
    # If `--pypi` flag has been passed, install from PyPI.
    if cli_options.pkg_manager == 'req_txt' and uv_available:
        if cli_options.pypi:
            make_sp_call("uv pip cache purge")
            make_sp_call(f"uv pip install --python {path_to_python} django-simple-deploy")
        else:
            make_sp_call(f"uv pip install --python {path_to_python} -e {sd_root_dir}")
    elif cli_options.pkg_manager == "req_txt":
        if cli_options.pypi:
            make_sp_call("pip cache purge")
            make_sp_call(f"{pip_path} install django-simple-deploy")
        else:
            make_sp_call(f"{pip_path} install -e {sd_root_dir}")


    elif cli_options.pkg_manager == 'poetry':
        # Use pip to install the local version.
        # We could install the local wheel file using `poetry add`, but then 
        #   the lock file won't work on the remote server. We're really testing
        #   how simple_deploy handles a poetry environment, we're not testing
        #   how poetry installs the local package. So this should reliably test
        #   whether an end user who uses poetry is able to use simple_deploy
        #   successfully.
        if cli_options.pypi:
            cmd = f". {activate_path} && cd {tmp_proj_dir} && poetry add django-simple-deploy"
            subprocess.run(cmd, shell=True, check=True)
        else:
            make_sp_call(f"{pip_path} install -e {sd_root_dir}")

    elif cli_options.pkg_manager == 'pipenv':
        if cli_options.pypi:
            cmd = f"cd {tmp_proj_dir} && . {activate_path} && pipenv install django-simple-deploy"
            subprocess.run(cmd, shell=True, check=True)
        else:
            # Install local (editable) version of django-simple-deploy.
            cmd = f"cd {tmp_proj_dir} && . {activate_path} && pipenv install -e {sd_root_dir}"# --skip-lock"
            subprocess.run(cmd, shell=True, check=True)

            # Rewrite the specification for dsd in Pipfile, so remote server
            #   won't try to install local version.
            pipfile_path = tmp_proj_dir / "Pipfile"
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
            cmd = f"cd {tmp_proj_dir} && . {activate_path} && pipenv lock"
            subprocess.run(cmd, shell=True, check=True)

    # Make an initial git commit, so we can reset the project every time we want
    #   to test a different simple_deploy command. This is much more efficient than
    #   tearing down the whole sample project and rebuilding it from scratch.
    # We use a git tag to do the reset, instead of trying to capture the initial hash.
    # Note: This tag refers to the version of the project that contains files for all
    #   dependency management systems, ie requirements.txt, pyproject.toml, and Pipfile.
    # Note: Current e2e tests don't reuse the project, but this is a very cheap step
    #   that makes the tmp project much more flexible in how we use it. For example, when
    #   dropping into this 
    git_exe = "git"
    os.chdir(tmp_proj_dir)
    make_sp_call("git init")
    make_sp_call("git branch -m main")
    make_sp_call("git add .")
    make_sp_call("git commit -am 'Initial commit.'")
    make_sp_call("git tag -am '' 'INITIAL_STATE'")

    # Add simple_deploy to INSTALLED_APPS.
    add_simple_deploy(tmp_proj_dir)

    # Make sure we have a clean status before calling simple_deploy.
    make_sp_call("git commit -am 'Added simple_deploy to INSTALLED_APPS.'")
