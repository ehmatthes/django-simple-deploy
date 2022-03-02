"""Simple unit tests for django-simple-deploy."""

from pathlib import Path

import pytest

@pytest.fixture(scope='module')
def settings_text(tmp_project):
    return Path(tmp_project / 'blog/settings.py').read_text()


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
