import subprocess
from pathlib import Path
from time import sleep

import pytest


@pytest.fixture(scope='session')
def tmp_project(tmp_path_factory):
    """Create a copy of the local sample project, so that platform-specific modules
    can call simple_deploy.

    Most tests will examine how the project was modified.
    """

    # Pause, or the tmpdir won't be usable.
    sleep(0.2)

    # Root directory of local simple_deploy project.
    sd_root_dir = Path(__file__).parent.parent
    tmp_proj_dir = tmp_path_factory.mktemp('blog_project')

    # To see where pytest creates the tmp_proj_dir, uncomment the following line.
    #   All tests will fail, but the AssertionError will show you the full path
    #   to tmp_proj_dir.
    # assert not tmp_proj_dir
    
    cmd = f'sh utils/setup_project.sh -d {tmp_proj_dir} -s {sd_root_dir}'
    cmd_parts = cmd.split()
    subprocess.run(cmd_parts)

    diag_fp = Path('/Users/eric/Desktop/diagnostic.txt')
    with open(diag_fp, 'w') as f:
        f.write("Hello from tmp_project.\n")
        f.write(f"{__file__}")

    # Return the location of the temp project.
    return tmp_proj_dir


@pytest.fixture(scope='module')
def reset_test_project(tmp_project, request):
    """Reset the test project, so it can be used again by another test module,
    which may be another platform.
    """
    sd_root_dir = Path(__file__).parents[3]
    cmd = f"sh utils/reset_test_project.sh {tmp_project}"
    cmd_parts = cmd.split()
    subprocess.run(cmd_parts)

    diag_fp = Path('/Users/eric/Desktop/diagnostic.txt')
    with open(diag_fp, 'a') as f:
        f.write("\n\nHello from test_project.\n")
        f.write(f"\n{request.module.__name__}")
        f.write(f"\n{request.path}")