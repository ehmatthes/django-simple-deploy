"""Check the response to various states of the user's repository.
"""

from pathlib import Path
import subprocess

import pytest

from ..utils import manage_sample_project as msp


# --- Fixtures ---

# --- Helper functions ---


# --- Test valid platform-agnostic simple_deploy calls ---

# def test_help_output(tmp_project, capfd):
#     """Call `manage.py simple_deploy --help`."""
#     valid_sd_command = "python manage.py simple_deploy --help"
#     stdout, stderr = msp.call_simple_deploy(tmp_project, valid_sd_command)

#     current_test_dir = Path(__file__).parent
#     reference_help_output = (current_test_dir / 'reference_files/sd_help_output.txt').read_text()

#     assert stdout == reference_help_output



# Notes: Test with --ignore-unclean-git.


def test_clean_git_status(tmp_project, capfd):
    """Call simple_deploy with the existing state of the project."""
    sd_command = "python manage.py simple_deploy --platform fly_io"
    stdout, stderr = msp.call_simple_deploy(tmp_project, sd_command)

    # This is only found if the git check passed.
    # DEV: Consider explicit output about git check that was run, or ignoring git status?
    assert   "Dependency management system: " in stdout

def test_unacceptable_git_status(tmp_project, capfd):
    """Call simple_deploy after adding a line to settings.py."""
    path = tmp_project / "blog" / "settings.py"
    assert path.exists()

    settings_text = path.read_text()
    new_text = "\n# Placeholder comment to create unacceptable git status."
    new_settings_text = settings_text + new_text
    path.write_text(new_settings_text)

    sd_command = "python manage.py simple_deploy --platform fly_io"
    stdout, stderr = msp.call_simple_deploy(tmp_project, sd_command)

    # This is only found if the git check passed.
    # DEV: Consider explicit output about git check that was run, or ignoring git status?
    assert   "Dependency management system: " not in stdout
    assert "SimpleDeployCommandError" in stderr