"""Simple unit tests for django-simple-deploy."""

# import subprocess
# from time import sleep
from pathlib import Path

import pytest


# @pytest.fixture(scope='module')
# def tmp_project(tmpdir_factory):
#     """Create a copy of the local sample project, and run simple_deploy
#     against this project. Most tests will examine how the project
#     was modified.
#     """

#     # Pause, or the tmpdir won't be usable.
#     sleep(0.2)

#     # Root directory of local simple_deploy project.
#     sd_root_dir = Path(__file__).parent.parent
#     tmp_proj_dir = tmpdir_factory.mktemp('blog_project')
#     cmd = f'sh setup_project.sh -d {tmp_proj_dir} -s {sd_root_dir}'
#     cmd_parts = cmd.split()
#     subprocess.run(cmd_parts)

#     # Return the location of the temp project.
#     return tmp_proj_dir


def test_creates_heroku_specific_settings_section(tmp_project):
    """Verify there's a Heroku-specific settings section."""
    settings_text = Path(tmp_project / 'blog/settings.py').read_text()
    assert "if 'ON_HEROKU' in os.environ:" in settings_text

# @pytest.mark.skip()
def test_imports_dj_database_url(tmp_project):    
    """Verify dj_database_url is imported."""
    settings_text = Path(tmp_project / 'blog/settings.py').read_text()
    assert "import dj_database_url" in settings_text