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

def test_creates_platformsh_specific_settings_section(run_simple_deploy, settings_text):
    """Verify there's a Platform.sh-specific settings section."""
    # Read lines from platform.sh settings template, and make sure these
    # lines are in the settings file. Remove whitespace from the lines before
    # checking.

    # Root directory of local simple_deploy project.
    sd_root_dir = Path(__file__).parent.parent
    path = sd_root_dir / 'simple_deploy/templates/platformsh_settings.py'
    lines = path.read_text().splitlines()
    for expected_line in lines[4:]:
        assert expected_line.strip() in settings_text

def test_creates_platform_app_yaml_file(tmp_project, run_simple_deploy):
    """Verify that .platform.app.yaml is created correctly."""

    # Root directory of local simple_deploy project.
    sd_root_dir = Path(__file__).parent.parent
    path_original = sd_root_dir / 'simple_deploy/templates/platform.app.yaml'
    original_text = path_original.read_text()
    path_generated = tmp_project / '.platform.app.yaml'
    generated_text = path_generated.read_text(encoding='utf-8')
    # Replace {{ project_name }} with test project name.
    expected_text = original_text.replace('{{ project_name }}', 'blog')

    assert generated_text == expected_text


