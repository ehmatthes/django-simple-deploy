"""Simple unit tests for django-simple-deploy."""

from pathlib import Path

import pytest


def test_creates_heroku_specific_settings_section(tmp_project):
    """Verify there's a Heroku-specific settings section."""
    settings_text = Path(tmp_project / 'blog/settings.py').read_text()
    assert "if 'ON_HEROKU' in os.environ:" in settings_text

def test_imports_dj_database_url(tmp_project):    
    """Verify dj_database_url is imported."""
    settings_text = Path(tmp_project / 'blog/settings.py').read_text()
    assert "import dj_database_url" in settings_text