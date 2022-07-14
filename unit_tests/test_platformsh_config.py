"""Simple unit tests for django-simple-deploy, targeting Platform.sh."""

from pathlib import Path
import subprocess

import pytest


# --- Fixtures ---

@pytest.fixture(scope='module')
def run_simple_deploy(tmp_project):
    # Call simple_deploy here, so it can target this module's platform.
    # cmd = f"sh call_simple_deploy.sh -d {tmp_project} -p platform_sh"
    cmd = f"sh call_simple_deploy.sh -d {tmp_project} -p platform_sh"
    cmd_parts = cmd.split()
    subprocess.run(cmd_parts)

@pytest.fixture(scope='module')
def settings_text(tmp_project):
    return Path(tmp_project / 'blog/settings.py').read_text()


# --- Test modifications to settings.py ---

def test_creates_heroku_specific_settings_section(run_simple_deploy, settings_text):
    """Verify there's a Heroku-specific settings section."""
    assert "from platformshconfig import Config" in settings_text

    # DEV: Does not seem to be calling simple_deploy --platform_sh
    # Calling for heroku works, for platform_sh doesn't seem to.