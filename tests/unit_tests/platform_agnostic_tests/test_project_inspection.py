"""Tests for how accurately we inspect the project.

Example: When we inspect the project, do we correctly identify the dependency
  management approach that's currently being used?
"""

from pathlib import Path
import subprocess

import pytest


# --- Fixtures ---

# --- Helper functions ---

def make_valid_call(tmp_proj_dir, valid_sd_command):
    """Make a valid call.
    Returns:
    - None
    """

    # We have to be careful about how we split cmd before passing it to subprocess.run(),
    #   because valid_sd_command has spaces in it. If we simply call cmd.split(), the command
    #   will be just "python
    # So, we need to split the first part of the command, and then append valid_sd_command.
    #   This keeps valid_sd_command as one argument.
    # DEV: Naming inconsistency; the existing call_simple_deploy_invalid.sh actually
    #   works for making valid test calls as well.
    cmd = f'sh utils/call_simple_deploy_invalid.sh {tmp_proj_dir}'
    cmd_parts = cmd.split()
    cmd_parts.append(valid_sd_command)
    subprocess.run(cmd_parts)


# --- Test correct identification of dependency management approach. ---

@pytest.mark.skip(reason="Write this test after logging inspection process.")
def test_identify_dep_man_approach(tmp_project, capfd):
    """Verify that we identified the correct dependency management approach
    that's currently being used.
    """
    valid_sd_command = "python manage.py simple_deploy --platform heroku"

    make_valid_call(tmp_project, valid_sd_command)
    captured = capfd.readouterr()

    # This should be a more specific test about the output related to identifying
    #   the dependency management approacht that was found.
    assert 'requirements.txt' not in captured.out