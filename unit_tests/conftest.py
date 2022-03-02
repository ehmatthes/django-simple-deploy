import subprocess
from pathlib import Path
from time import sleep

import pytest


@pytest.fixture(scope='module')
def tmp_project(tmpdir_factory):
    """Create a copy of the local sample project, and run simple_deploy
    against this project. Most tests will examine how the project
    was modified.
    """

    # Pause, or the tmpdir won't be usable.
    sleep(0.2)

    # Root directory of local simple_deploy project.
    sd_root_dir = Path(__file__).parent.parent
    tmp_proj_dir = tmpdir_factory.mktemp('blog_project')
    cmd = f'sh setup_project.sh -d {tmp_proj_dir} -s {sd_root_dir}'
    cmd_parts = cmd.split()
    subprocess.run(cmd_parts)

    # Return the location of the temp project.
    return tmp_proj_dir