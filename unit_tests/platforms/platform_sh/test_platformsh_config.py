"""Unit tests for django-simple-deploy, targeting Platform.sh."""

from pathlib import Path
import subprocess

import pytest

import unit_tests.utils.ut_helper_functions as hf


# --- Fixtures ---

@pytest.fixture(scope='module')
def run_simple_deploy(reset_test_project, tmp_project):
    # Call simple_deploy here, so it can target this module's platform.
    sd_root_dir = Path(__file__).parents[3]
    cmd = f"sh utils/call_simple_deploy.sh -d {tmp_project} -p platform_sh -s {sd_root_dir}"
    cmd_parts = cmd.split()
    subprocess.run(cmd_parts)


# --- Test modifications to project files. ---

def test_settings(tmp_project, run_simple_deploy):
    """Verify settings have been changed for Platform.sh."""
    hf.check_reference_file(tmp_project, 'blog/settings.py', 'platform_sh')

def test_requirements_txt(tmp_project, run_simple_deploy):
    """Test that the requirements.txt file is correct."""
    hf.check_reference_file(tmp_project, 'requirements.txt', 'platform_sh')

def test_gitignore(tmp_project, run_simple_deploy):
    """Test that .gitignore has been modified correctly."""
    hf.check_reference_file(tmp_project, '.gitignore', 'platform_sh')


# --- Test Platform.sh yaml files ---

def test_platform_app_yaml_file(tmp_project, run_simple_deploy):
    hf.check_reference_file(tmp_project, '.platform.app.yaml', 'platform_sh')

def test_services_yaml_file(tmp_project, run_simple_deploy):
    hf.check_reference_file(tmp_project, '.platform/services.yaml', 'platform_sh')


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
