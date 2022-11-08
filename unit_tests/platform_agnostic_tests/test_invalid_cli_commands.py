from pathlib import Path
import subprocess

import pytest


# --- Fixtures ---


# --- Test modifications to settings.py ---

# def test_bare_call(tmp_project, capfd):
#     """Call simple_deploy with no arguments."""
#     arg_string = ""
#     # cmd = f"sh utils/call_simple_deploy_invalid.sh -d {tmp_project} -a {arg_string}"
#     cmd = f"sh utils/call_simple_deploy_invalid.sh -d {tmp_project}"
#     cmd_parts = cmd.split()
#     subprocess.run(cmd_parts)
#     captured = capfd.readouterr()

#     assert "The --platform flag is required;" in captured.err
#     assert "Please re-run the command with a --platform option specified." in captured.err
#     assert "$ python manage.py simple_deploy --platform platform_sh" in captured.err

# def test_invalid_platform_call(tmp_project, capfd):
#     """Call simple_deploy with an invalid --platform argument."""
#     arg_string = "--platform unsupported_platform_name"
#     cmd = f"sh utils/call_simple_deploy_invalid.sh -d {tmp_project} -a {arg_string}"
#     # cmd = f"sh utils/call_simple_deploy_invalid.sh -d {tmp_project}"
#     cmd_parts = cmd.split()
#     subprocess.run(cmd_parts)
#     captured = capfd.readouterr()

#     # assert not cmd
#     assert "The platform unsupported_platform_name is not currently supported." in captured.err



def test_invalid_platform_call(tmp_project, capfd):
    """Call simple_deploy with an invalid --platform argument."""
    invalid_sd_command = "python manage.py simple_deploy --unit-testing --platform unsupported_platform_name"

    diagnostic_file = tmp_project / "diagnostics.txt"

    # cmd = f'sh utils/call_simple_deploy_invalid.sh {tmp_project} "{invalid_sd_command}"'
    # diagnostic_file.write_text(cmd)

    # We have to be careful about how we split cmd before passing it to subprocess.run(),
    #   because invalid_sd_command has spaces in it. If we simply call cmd.split(), the command
    #   will be just "python
    # So, we need to split the first part of the command, and then append invalid_sd_command.
    #   This keeps invalid_sd_command as one argument.
    cmd = f'sh utils/call_simple_deploy_invalid.sh {tmp_project}'
    cmd_parts = cmd.split()
    cmd_parts.append(invalid_sd_command)
    diagnostic_file.write_text(str(cmd_parts))







    # cmd_parts = cmd.split()
    subprocess.run(cmd_parts)
    captured = capfd.readouterr()

    # assert not cmd
    assert "The platform unsupported_platform_name is not currently supported." in captured.err
