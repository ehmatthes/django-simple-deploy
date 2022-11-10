"""Unit tests for django-simple-deploy, targeting Fly.io."""

from pathlib import Path
import subprocess

import pytest

import unit_tests.utils.ut_helper_functions as hf


# --- Fixtures ---

@pytest.fixture(scope='module')
def run_simple_deploy(reset_test_project, tmp_project):
    # Call simple_deploy here, so it can target this module's platform.
    sd_root_dir = Path(__file__).parents[3]
    cmd = f"sh utils/call_simple_deploy.sh -d {tmp_project} -p fly_io -s {sd_root_dir}"
    cmd_parts = cmd.split()
    subprocess.run(cmd_parts)


# --- Test modifications to project files. ---

def test_settings(tmp_project, run_simple_deploy):
    """Verify there's a Fly.io-specific settings section.
    This function only checks the entire settings file. It does not examine
      individual settings.
    """
    hf.check_reference_file(tmp_project, 'blog/settings.py', 'fly_io')

def test_requirements_txt(tmp_project, run_simple_deploy):
    """Test that the requirements.txt file is correct."""
    hf.check_reference_file(tmp_project, 'requirements.txt', 'fly_io')

def test_gitignore(tmp_project, run_simple_deploy):
    """Test that .gitignore has been modified correctly."""
    hf.check_reference_file(tmp_project, '.gitignore', 'fly_io')


# --- Test Fly.io-specific files ---

def test_creates_fly_toml_file(tmp_project, run_simple_deploy):
    """Verify that fly.toml is created correctly."""
    hf.check_reference_file(tmp_project, 'fly.toml', 'fly_io')

def test_creates_dockerfile(tmp_project, run_simple_deploy):
    """Verify that dockerfile is created correctly."""
    hf.check_reference_file(tmp_project, 'Dockerfile', 'fly_io')

def test_creates_dockerignore_file(tmp_project, run_simple_deploy):
    """Verify that dockerignore file is created correctly."""
    hf.check_reference_file(tmp_project, '.dockerignore', 'fly_io')


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

    # Read log file. We can never just examine the log file directly to a reference,
    #   because it will have different timestamps.
    # If we need to, we can make a comparison of all content except timestamps.
    # DEV: Look for specific log file; not sure this log file is always the second one.
    #   We're looking for one similar to "simple_deploy_2022-07-09174245.log".
    log_file = log_files[0]   # update on friendly summary
    log_file_text = log_file.read_text()

    # DEV: Update these for more platform-specific log messages.
    # Spot check for opening log messages.
    assert "INFO: Logging run of `manage.py simple_deploy`..." in log_file_text
    assert "INFO: Configuring project for deployment to Fly.io..." in log_file_text

    # Spot check for success messages.
    assert "INFO: --- Your project is now configured for deployment on Fly.io ---" in log_file_text
    assert "INFO: To deploy your project, you will need to:" in log_file_text
