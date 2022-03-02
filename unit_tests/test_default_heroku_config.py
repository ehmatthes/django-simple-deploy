"""Simple unit tests for django-simple-deploy."""

from pathlib import Path
import subprocess

import pytest


# --- Fixtures ---

@pytest.fixture(scope='module')
def settings_text(tmp_project):
    return Path(tmp_project / 'blog/settings.py').read_text()


# --- Test modifications to settings.py ---

def test_creates_heroku_specific_settings_section(settings_text):
    """Verify there's a Heroku-specific settings section."""
    assert "if 'ON_HEROKU' in os.environ:" in settings_text

def test_imports_dj_database_url(settings_text):    
    """Verify dj_database_url is imported."""
    assert "import dj_database_url" in settings_text

def test_allowed_hosts(settings_text):
    """Verify sample project is in ALLOWED_HOSTS."""
    assert "    ALLOWED_HOSTS.append('sample-name-11894.herokuapp.com')" in settings_text

def test_databases_setting(settings_text):
    """Verify DATABASES settings is correct."""
    assert "    DATABASES = {'default': dj_database_url.config(default='postgres://localhost')}" in settings_text

def test_static_root_setting(settings_text):
    """Verify the STATIC_ROOT setting is correct."""
    assert "    STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')" in settings_text

def test_static_url_setting(settings_text):
    """Verify the STATIC_URL setting is correct."""
    assert "    STATIC_URL = '/static/'" in settings_text

def test_staticfiles_dirs_setting(settings_text):
    """Verify the STATICFILES_DIRS setting is correct."""
    assert "    STATICFILES_DIRS = (os.path.join(BASE_DIR, 'static'),)" in settings_text

def test_debug_setting(settings_text):
    """Verify the DEBUG setting is correct."""
    assert "    DEBUG = os.getenv('DEBUG') == 'TRUE'" in settings_text

def test_secret_key_setting(settings_text):
    """Verify the SECRET_KEY setting is correct."""
    assert "    SECRET_KEY = os.getenv('SECRET_KEY')" in settings_text


# --- Test Procfile ---

def test_generated_procfile(tmp_project):
    """Test that the generated Procfile is correct."""
    procfile_text = Path(tmp_project / 'Procfile').read_text()
    assert "web: gunicorn blog.wsgi --log-file -" in procfile_text


# --- Test requirements.txt ---

def test_requirements_txt_file(tmp_project):
    """Test that the requirements.txt file is correct."""
    rt_text = Path(tmp_project / 'requirements.txt').read_text()
    assert "django-simple-deploy          # Added by simple_deploy command." in rt_text
    assert "gunicorn                      # Added by simple_deploy command." in rt_text
    assert "psycopg2<2.9                  # Added by simple_deploy command." in rt_text
    assert "dj-database-url               # Added by simple_deploy command." in rt_text
    assert "whitenoise                    # Added by simple_deploy command." in rt_text


# --- Test logs ---

def test_log_dir(tmp_project):
    """Test that the log directory exists, and contains an appropriate log file."""
    log_path = Path(tmp_project / 'simple_deploy_logs')
    assert log_path.exists()

    # There should be exactly one log file.
    log_files = sorted(log_path.glob('*'))
    assert len(log_files) == 1

    # Read log file.
    log_file = log_files[0]
    log_file_text = log_file.read_text()

    # Spot check for opening log messages.
    assert "INFO: Logging run of `manage.py simple_deploy`..." in log_file_text
    assert "INFO: Configuring project for deployment to Heroku..." in log_file_text

    # Spot check for success messages.
    assert "INFO: --- Your project is now configured for deployment on Heroku. ---" in log_file_text
    assert "INFO: Or, you can visit https://sample-name-11894.herokuapp.com." in log_file_text

def test_ignore_log_dir(tmp_project):
    """Check that git is ignoring the log directory."""
    gitignore_text = Path(tmp_project / '.gitignore').read_text()
    assert 'simple_deploy_logs/' in gitignore_text


# --- Test staticfile setup ---

def test_static_dir(tmp_project):
    """Test that static dir exists, and contains placeholder file."""
    static_path = Path(tmp_project / 'static')
    assert static_path.exists()

    # There should be exactly one file in static/.
    static_dir_files = sorted(static_path.glob('*'))
    assert len(static_dir_files) == 1

    # We should find placeholder.txt.
    static_dir_file = static_dir_files[0]
    assert static_dir_file.name == 'placeholder.txt'

    # It should contain one line.
    assert static_dir_file.read_text() == 'This is a placeholder file to make sure this folder is pushed to Heroku.'


# --- Test Heroku host already in ALLOWED_HOSTS ---

def test_heroku_host_in_allowed_hosts(tmp_project):
    """Test that no ALLOWED_HOST entry in Heroku-specific settings if the
    Heroku host is already in ALLOWED_HOSTS.
    """
    # Modify the test project, and rerun simple_deploy.
    cmd = f'sh modify_allowed_hosts.sh -d {tmp_project}'
    cmd_parts = cmd.split()
    subprocess.run(cmd_parts)

    # Check that there's no ALLOWED_HOSTS setting in the Heroku-specific settings.
    #   If we use the settings_text fixture, we'll get the original settings text
    #   because it has module-level scope.
    settings_text = Path(tmp_project / 'blog/settings.py').read_text()
    assert "    ALLOWED_HOSTS.append('sample-name-11894.herokuapp.com')" not in settings_text