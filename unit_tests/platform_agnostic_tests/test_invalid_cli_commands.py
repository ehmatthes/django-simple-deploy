from pathlib import Path
import subprocess

import pytest


# --- Fixtures ---


# --- Test modifications to settings.py ---

def test_bare_call(tmp_project, capfd):
    """Call simple_deploy with no arguments."""
    arg_string = ""
    # cmd = f"sh utils/call_simple_deploy_invalid.sh -d {tmp_project} -a {arg_string}"
    cmd = f"sh utils/call_simple_deploy_invalid.sh -d {tmp_project}"
    cmd_parts = cmd.split()
    subprocess.run(cmd_parts)
    captured = capfd.readouterr()

    assert "The --platform flag is required;" in captured.err
    assert "Please re-run the command with a --platform option specified." in captured.err
    assert "$ python manage.py simple_deploy --platform platform_sh" in captured.err