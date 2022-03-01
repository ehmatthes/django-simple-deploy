"""Simple unit tests for django-simple-deploy."""

import subprocess
from time import sleep
from pathlib import Path


def test_hello():
    assert 2 == 2

def run_command(cmd, use_shell=True):
    """Run a command through subprocess."""
    cmd_parts = cmd.split()
    output = subprocess.run(cmd_parts, capture_output=True)
    print(output)

def test_tmp_dir(tmpdir):

    sleep(0.2)

    source_directory = Path(__file__).parent.parent / 'vendor'

    cmd = f'sh setup_project.sh -d {tmpdir} -s {source_directory}'
    run_command(cmd)

    print(tmpdir)
    assert 0