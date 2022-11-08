import subprocess
from pathlib import Path
from time import sleep

import pytest


@pytest.fixture(scope='module')
def tmp_project(tmp_path_factory):
    """Create a copy of the local *minimal* sample project, so that test modules
    can call simple_deploy.

    Most tests will examine how the project was modified.
    """

    # Pause, or the tmpdir won't be usable.
    sleep(0.2)

    # Root directory of local simple_deploy project.
    sd_root_dir = Path(__file__).parents[2]
    tmp_proj_dir = tmp_path_factory.mktemp('mysite')

    # To see where pytest creates the tmp_proj_dir, uncomment the following line.
    #   All tests will fail, but the AssertionError will show you the full path
    #   to tmp_proj_dir.
    # assert not tmp_proj_dir
    
    cmd = f'sh utils/setup_minimal_project.sh -d {tmp_proj_dir} -s {sd_root_dir}'
    cmd_parts = cmd.split()
    subprocess.run(cmd_parts)

    # Return the location of the temp project.
    return tmp_proj_dir