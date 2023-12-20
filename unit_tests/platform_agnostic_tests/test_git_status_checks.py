"""Check the response to various states of the user's repository.
"""

from pathlib import Path
import subprocess

import pytest

from ..utils import manage_sample_project as msp


# --- Fixtures ---

# --- Helper functions ---

# --- Test against various valid and invalid states of user's project. ---

def test_clean_git_status(tmp_project, capfd):
    """Call simple_deploy with the existing state of the project."""
    sd_command = "python manage.py simple_deploy --platform fly_io"
    stdout, stderr = msp.call_simple_deploy(tmp_project, sd_command)

    # This is only found if the git check passed.
    # DEV: Consider explicit output about git check that was run, or ignoring git status?
    assert   "Dependency management system: " in stdout

def test_unacceptable_settings_change(tmp_project, capfd):
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

def test_simple_deploy_logs_exists(tmp_project, capfd):
    log_dir = tmp_project / "simple_deploy_logs"
    log_dir.mkdir()
    assert log_dir.exists()

    log_path = log_dir / "dummy_log.log"
    log_path.write_text("Dummy log entry.")
    assert log_path.exists()

    sd_command = "python manage.py simple_deploy --platform fly_io"
    stdout, stderr = msp.call_simple_deploy(tmp_project, sd_command)

    # This is only found if the git check passed.
    # DEV: Consider explicit output about git check that was run, or ignoring git status?
    assert   "Dependency management system: " in stdout