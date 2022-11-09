from pathlib import Path
import subprocess

import pytest


# --- Fixtures ---

@pytest.fixture(scope="module", autouse=True)
def commit_test_project(tmp_project):
    """Start each test run with a clean git status.
    The initial project state has an unclean status, after adding simple_deploy
      to INSTALLED_APPS. It's much easier to verify that these invalid commands
      leave the project unchanged if we simply start with a clean git status.
    Returns:
    - None
    """
    commit_msg = "Start with clean state before calling invalid command."
    cmd = f"sh utils/commit_test_project.sh {tmp_project}"
    cmd_parts = cmd.split()
    cmd_parts.append(commit_msg)
    subprocess.run(cmd_parts)


# --- Helper functions ---

def make_invalid_call(tmp_proj_dir, invalid_sd_command):
    """Make an invalid call.
    Returns:
    - None
    """

    # We have to be careful about how we split cmd before passing it to subprocess.run(),
    #   because invalid_sd_command has spaces in it. If we simply call cmd.split(), the command
    #   will be just "python
    # So, we need to split the first part of the command, and then append invalid_sd_command.
    #   This keeps invalid_sd_command as one argument.
    cmd = f'sh utils/call_simple_deploy_invalid.sh {tmp_proj_dir}'
    cmd_parts = cmd.split()
    cmd_parts.append(invalid_sd_command)
    subprocess.run(cmd_parts)


def call_git_status(tmp_proj_dir):
    """Call git status."""
    cmd = f"sh utils/call_git_status.sh {tmp_proj_dir}"
    cmd_parts = cmd.split()
    subprocess.run(cmd_parts)


# --- Test modifications to settings.py ---

def test_bare_call(tmp_project, capfd):
    """Call simple_deploy with no arguments."""
    invalid_sd_command = "python manage.py simple_deploy"

    make_invalid_call(tmp_project, invalid_sd_command)
    captured = capfd.readouterr()

    assert "The --platform flag is required;" in captured.err
    assert "Please re-run the command with a --platform option specified." in captured.err
    assert "$ python manage.py simple_deploy --platform platform_sh" in captured.err

    call_git_status(tmp_project)
    captured = capfd.readouterr()
    assert "On branch main\nnothing to commit, working tree clean" in captured.out
    assert "nothing to commit, working tree clean" in captured.out


def test_invalid_platform_call(tmp_project, capfd):
    """Call simple_deploy with an invalid --platform argument."""
    invalid_sd_command = "python manage.py simple_deploy --platform unsupported_platform_name"

    make_invalid_call(tmp_project, invalid_sd_command)
    captured = capfd.readouterr()

    assert "The platform unsupported_platform_name is not currently supported." in captured.err

    call_git_status(tmp_project)
    captured = capfd.readouterr()
    assert "On branch main\nnothing to commit, working tree clean" in captured.out
    assert "nothing to commit, working tree clean" in captured.out
