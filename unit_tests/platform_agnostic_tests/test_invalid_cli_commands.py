from pathlib import Path
import subprocess

import pytest


# --- Fixtures ---


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


# --- Test modifications to settings.py ---

def test_bare_call(tmp_project, capfd):
    """Call simple_deploy with no arguments."""
    invalid_sd_command = "python manage.py simple_deploy"

    make_invalid_call(tmp_project, invalid_sd_command)
    captured = capfd.readouterr()

    assert "The --platform flag is required;" in captured.err
    assert "Please re-run the command with a --platform option specified." in captured.err
    assert "$ python manage.py simple_deploy --platform platform_sh" in captured.err


def test_invalid_platform_call(tmp_project, capfd):
    """Call simple_deploy with an invalid --platform argument."""
    invalid_sd_command = "python manage.py simple_deploy --platform unsupported_platform_name"

    make_invalid_call(tmp_project, invalid_sd_command)
    captured = capfd.readouterr()

    assert "The platform unsupported_platform_name is not currently supported." in captured.err
