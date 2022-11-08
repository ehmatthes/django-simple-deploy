from pathlib import Path
import subprocess

import pytest


# --- Fixtures ---

# @pytest.fixture(scope='module')
# def run_simple_deploy(tmp_project):
#     # Call simple_deploy here, so it can target this module's platform.
#     # cmd = f"sh call_simple_deploy.sh -d {tmp_project} -p platform_sh"
#     sd_root_dir = Path(__file__).parents[3]
#     cmd = f"sh utils/call_simple_deploy.sh -d {tmp_project} -p platform_sh -s {sd_root_dir}"
#     cmd_parts = cmd.split()
#     subprocess.run(cmd_parts)


# --- Test modifications to settings.py ---

# def test_creates_platformsh_specific_settings_section(run_simple_deploy, settings_text):
#     """Verify there's a Platform.sh-specific settings section."""
#     # Read lines from platform.sh settings template, and make sure these
#     # lines are in the settings file. Remove whitespace from the lines before
#     # checking.

#     # Root directory of local simple_deploy project.
#     sd_root_dir = Path(__file__).parents[3]
#     path = sd_root_dir / 'simple_deploy/templates/platformsh_settings.py'
#     lines = path.read_text().splitlines()
#     for expected_line in lines[4:]:
#         assert expected_line.strip() in settings_text


# DEV: This is what I want to call in each test in this module.
# # Call invalid version of simple_deploy, to test the results before
# #   making a valid call. This should error out, without changing project.
# # DEV: Move this to a separate test function; test for specific error msg.
# cmd = f"sh utils/call_sd_no_platform.sh -d {tmp_proj_dir}"
# cmd_parts = cmd.split()
# result = subprocess.run(cmd_parts)
# assert result.returncode == 1


def test_bare_call(tmp_project, capfd):
    """Call simple_deploy with no arguments."""
    arg_string = ""
    # cmd = f"sh utils/call_simple_deploy_invalid.sh -d {tmp_project} -a {arg_string}"
    cmd = f"sh utils/call_simple_deploy_invalid.sh -d {tmp_project}"
    cmd_parts = cmd.split()
    subprocess.run(cmd_parts)
    # assert False
    # captured = capsys.readouterr()
    # assert '' == captured
    # assert '' == capfd.readouterr()
    # captured = capsys.readouterr()
    # assert "The --platform flag is required" in captured.err
    captured = capfd.readouterr()
    # assert not captured
    # assert "The --platform flag is required;" in captured.out
    # assert "Please re-run the command with a --platform option specified." in captured.out
    # assert not type(captured.out)

    assert "The --platform flag is required;" in captured.err
    assert "Please re-run the command with a --platform option specified." in captured.err