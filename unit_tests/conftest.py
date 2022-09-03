import subprocess
from pathlib import Path
from time import sleep

import pytest


@pytest.fixture(scope='module')
def tmp_project(tmpdir_factory):
    """Create a copy of the local sample project, so that platform-specific modules
    can call simple_deploy.

    Most tests will examine how the project was modified.
    """

    # Pause, or the tmpdir won't be usable.
    sleep(0.2)

    # Root directory of local simple_deploy project.
    sd_root_dir = Path(__file__).parent.parent
    tmp_proj_dir = tmpdir_factory.mktemp('blog_project')
    cmd = f'sh setup_project.sh -d {tmp_proj_dir} -s {sd_root_dir}'
    cmd_parts = cmd.split()
    subprocess.run(cmd_parts)

    # Call invalid version of simple_deploy, to test the results before
    #   making a valid call. This should error out, without changing project.
    # DEV: Move this to a separate test function; test for specific error msg.
    cmd = f"sh call_sd_no_platform.sh -d {tmp_proj_dir}"
    cmd_parts = cmd.split()
    result = subprocess.run(cmd_parts)
    assert result.returncode == 1

    # Return the location of the temp project.
    return tmp_proj_dir