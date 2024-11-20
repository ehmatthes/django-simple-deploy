"""Check behavior when finding an existing file we want to replace.

Should be able to use any valid platform for these calls.
"""

from pathlib import Path
import subprocess, shlex, os, sys

import pytest

from ..utils import manage_sample_project as msp


# --- Helper functions ---


def execute_quick_command(tmp_project, cmd):
    """Run a quick command, and return CompletedProcess object."""
    cmd_parts = shlex.split(cmd)
    os.chdir(tmp_project)
    return subprocess.run(cmd_parts, capture_output=True)


# --- Test functions ---


def test_with_existing_dockerfile(tmp_project):
    """Call simple_deploy with an existing Dockerfile.

    The --unit-testing flag should get confirmation, but we should see a relevant
    message in the log.
    """
    path_dockerfile = tmp_project / "Dockerfile"
    path_dockerfile.write_text("Dummy dockerfile for testing.")

    cmd = "git add Dockerfile"
    output_str = execute_quick_command(tmp_project, cmd).stdout.decode()
    cmd = "git commit -am 'Added dummy dockerfile.'"
    output_str = execute_quick_command(tmp_project, cmd).stdout.decode()

    sd_command = "python manage.py deploy"
    stdout, stderr = msp.call_simple_deploy(tmp_project, sd_command)

    assert (
        "The file Dockerfile already exists. Is it okay to replace this file?" in stdout
    )
