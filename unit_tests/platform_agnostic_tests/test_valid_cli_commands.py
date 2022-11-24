"""Check the output of valid platform-agnostic cli commands.
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


# --- Test valid platform-agnostic simple_deploy calls ---

def test_help_output(tmp_project, capfd):
    """Call `manage.py simple_deploy --help`."""
    valid_sd_command = "python manage.py simple_deploy --help"

    make_valid_call(tmp_project, valid_sd_command)
    captured = capfd.readouterr()

    reference_help_output = Path('platform_agnostic_tests/reference_files/sd_help_output.txt').read_text()
    assert captured.out == reference_help_output
