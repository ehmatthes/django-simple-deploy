import os
import subprocess
import sys
from pathlib import Path
from shutil import copytree

def setup_project(tmp_proj_dir, sd_root_dir):
    sample_project_dir = sd_root_dir / "sample_project/blog_project"
    copytree(sample_project_dir, tmp_proj_dir, dirs_exist_ok=True)

    venv_dir = tmp_proj_dir / "b_env"
    subprocess.run([sys.executable, "-m", "venv", venv_dir])

    pip_path = venv_dir / ("Scripts" if os.name == "nt" else "bin") / "pip"
    requirements_path = tmp_proj_dir / "requirements.txt"
    subprocess.run([pip_path, "install", "--no-index", "--find-links", sd_root_dir / "vendor", "-r", requirements_path])

    subprocess.run([pip_path, "install", "-e", sd_root_dir])
    assert False

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
