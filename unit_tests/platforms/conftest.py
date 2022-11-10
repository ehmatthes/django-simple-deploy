from pathlib import Path
import subprocess

import pytest


@pytest.fixture(scope='module')
def reset_test_project(tmp_project):
    """Reset the test project, so it can be used again by another test module,
    which may be another platform.
    """
    sd_root_dir = Path(__file__).parents[3]
    cmd = f"sh utils/reset_test_project.sh {tmp_project}"
    cmd_parts = cmd.split()
    subprocess.run(cmd_parts)