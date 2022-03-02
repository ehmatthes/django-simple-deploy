"""Simple unit tests for django-simple-deploy."""

import subprocess
from time import sleep
from pathlib import Path


def run_command(cmd, use_shell=True):
    """Run a command through subprocess."""
    cmd_parts = cmd.split()
    subprocess.run(cmd_parts)


def test_tmp_dir(tmpdir):

    # Pause, or the tmpdir won't be usable.
    sleep(0.2)

    # Root directory of local simple_deploy project.
    sd_root_dir = Path(__file__).parent.parent
    cmd = f'sh setup_project.sh -d {tmpdir} -s {sd_root_dir}'
    run_command(cmd)

    # Verify there's a Heroku-specific settings section.
    settings_text = Path(tmpdir / 'blog/settings.py').read_text()
    assert "if 'ON_HEROKU' in os.environ:" in settings_text

    # Verify correct database import.
    settings_text = Path(tmpdir / 'blog/settings.py').read_text()
    assert "import dj_database_url" in settings_text