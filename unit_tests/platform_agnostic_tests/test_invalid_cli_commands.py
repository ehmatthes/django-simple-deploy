"""Check that simple_deploy responds appropriately to invalid CLI calls.

Each test function makes an invalid call, and then checks that:
- Appropriately informative error messages are displayed to the end user.
- The user's project is unchanged.

Each test function includes the exact invalid call we expect users might make;
  the --unit-testing flag is added in the call_simple_deploy() function.
"""

from pathlib import Path
import subprocess

import pytest

from ..utils import manage_sample_project as msp


# --- Fixtures ---


# --- Helper functions ---

def check_project_unchanged(tmp_proj_dir):
    """Check that the project has not been changed.
    Checks git status and git log.
    """

    stdout, stderr = msp.make_git_call(tmp_proj_dir, "git status")
    assert "On branch main\nnothing to commit, working tree clean" in stdout

    stdout, stderr = msp.make_git_call(tmp_proj_dir, "git log")
    assert "Removed unneeded dependency management files." in stdout
    assert "Added simple_deploy to INSTALLED_APPS." in stdout


# --- Test invalid variations of the `simple_deploy` command ---

def test_bare_call(tmp_project):
    """Call simple_deploy with no arguments."""
    invalid_sd_command = "python manage.py simple_deploy"
    stdout, stderr = msp.call_simple_deploy(tmp_project, invalid_sd_command)

    assert "The --platform flag is required;" in stderr
    assert "Please re-run the command with a --platform option specified." in stderr
    assert "$ python manage.py simple_deploy --platform fly_io" in stderr
    check_project_unchanged(tmp_project)


def test_invalid_platform_call(tmp_project):
    """Call simple_deploy with an invalid --platform argument."""
    invalid_sd_command = "python manage.py simple_deploy --platform unsupported_platform_name"
    stdout, stderr = msp.call_simple_deploy(tmp_project, invalid_sd_command)

    assert 'The platform "unsupported_platform_name" is not currently supported.' in stderr
    check_project_unchanged(tmp_project)


def test_invalid_platform_call_automate_all(tmp_project):
    """Call simple_deploy with an invalid --platform argument,
    and `--automate-all`.
    """
    invalid_sd_command = "python manage.py simple_deploy --platform unsupported_platform_name --automate-all"
    stdout, stderr = msp.call_simple_deploy(tmp_project, invalid_sd_command)

    assert 'The platform "unsupported_platform_name" is not currently supported.' in stderr
    check_project_unchanged(tmp_project)