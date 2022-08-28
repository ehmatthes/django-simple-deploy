"""Simple unit tests for django-simple-deploy, targeting Platform.sh."""

from pathlib import Path
import subprocess

import pytest


# --- Fixtures ---

@pytest.fixture(scope='module')
def run_simple_deploy(tmp_project):
    # Call simple_deploy here, so it can target this module's platform.
    # cmd = f"sh call_simple_deploy.sh -d {tmp_project} -p platform_sh"
    sd_root_dir = Path(__file__).parent.parent
    cmd = f"sh call_simple_deploy.sh -d {tmp_project} -p platform_sh -s {sd_root_dir}"
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


# --- Test Platform.sh yaml files ---

def test_creates_platform_app_yaml_file(tmp_project, run_simple_deploy):
    """Verify that .platform.app.yaml is created correctly."""

    # Root directory of local simple_deploy project.
    sd_root_dir = Path(__file__).parent.parent

    # From the template, generate the expected file.
    path_original = sd_root_dir / 'simple_deploy/templates/platform.app.yaml'
    original_text = path_original.read_text()
    expected_text = original_text.replace('{{ project_name }}', 'blog')
    expected_text = expected_text.replace('{{ deployed_project_name }}', 'my_blog_project')

    # Get the actual file from the modified test project.
    path_generated = tmp_project / '.platform.app.yaml'
    generated_text = path_generated.read_text(encoding='utf-8')

    assert generated_text == expected_text

def test_routes_yaml_file(tmp_project, run_simple_deploy):
    """Verify that .platform/routes.yaml file is correct."""

    # Root directory of local simple_deploy project.
    sd_root_dir = Path(__file__).parent.parent

    # From the template, generate the expected file.
    path_original = sd_root_dir / 'simple_deploy/templates/routes.yaml'
    original_text = path_original.read_text()
    expected_text = original_text.replace('{{ project_name }}', 'my_blog_project')

    # Get the actual file from the modified test project.
    path_generated = tmp_project / '.platform/routes.yaml'
    generated_text = path_generated.read_text(encoding='utf-8')

    assert generated_text == expected_text

def test_services_yaml_file(tmp_project, run_simple_deploy):
    """Verify that .platform/services.yaml file is correct."""

    # Root directory of local simple_deploy project.
    sd_root_dir = Path(__file__).parent.parent

    # From the template, generate the expected file.
    path_original = sd_root_dir / 'simple_deploy/templates/services.yaml'
    # This file is the same for all projects.
    expected_text = path_original.read_text()

    # Get the actual file from the modified test project.
    path_generated = tmp_project / '.platform/services.yaml'
    generated_text = path_generated.read_text(encoding='utf-8')

    assert generated_text == expected_text


# --- Test requirements.txt ---

def test_requirements_txt_file(tmp_project, run_simple_deploy):
    """Test that the requirements.txt file is correct."""
    rt_text = Path(tmp_project / 'requirements.txt').read_text()
    assert "django-simple-deploy          # Added by simple_deploy command." in rt_text
    assert "platformshconfig              # Added by simple_deploy command." in rt_text
    assert "gunicorn                      # Added by simple_deploy command." in rt_text
    assert "psycopg2                      # Added by simple_deploy command." in rt_text


# --- Test logs ---

def test_log_dir(run_simple_deploy, tmp_project):
    """Test that the log directory exists, and contains an appropriate log file."""
    log_path = Path(tmp_project / 'simple_deploy_logs')
    assert log_path.exists()

    # DEV: After implementing friendly summary for Platform.sh, this file 
    #   will need to be updated.
    # There should be exactly two log files.
    log_files = sorted(log_path.glob('*'))
    log_filenames = [lf.name for lf in log_files]
    # Check for exactly the log files we expect to find.
    # assert 'deployment_summary.html' in log_filenames
    # DEV: Add a regex text for a file like "simple_deploy_2022-07-09174245.log".
    assert len(log_files) == 1   # update on friendly summary

    # Read log file.
    # DEV: Look for specific log file; not sure this log file is always the second one.
    #   We're looking for one similar to "simple_deploy_2022-07-09174245.log".
    log_file = log_files[0]   # update on friendly summary
    log_file_text = log_file.read_text()

    # DEV: Update these for more platform-specific log messages.
    # Spot check for opening log messages.
    assert "INFO: Logging run of `manage.py simple_deploy`..." in log_file_text
    assert "INFO: Configuring project for deployment to Platform.sh..." in log_file_text

    # Spot check for success messages.
    assert "INFO: --- Your project is now configured for deployment on Platform.sh. ---" in log_file_text
    assert "INFO: To deploy your project, you will need to:" in log_file_text

def test_ignore_log_dir(run_simple_deploy, tmp_project):
    """Check that git is ignoring the log directory."""
    gitignore_text = Path(tmp_project / '.gitignore').read_text()
    assert 'simple_deploy_logs/' in gitignore_text
