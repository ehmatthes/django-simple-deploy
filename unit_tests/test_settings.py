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

