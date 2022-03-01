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

    sleep(1)


    # run_command(f"cd {tmpdir}")
    # run_command('touch hello_pytest.txt')



    # cmd = f"cd {tmpdir}"
    # subprocess.run(cmd.split())
    # subprocess.run(['pwd'])
    # # subprocess.run('python3 -m venv tmp_env')
    # subprocess.run('touch hello_pytest.txt'.split())


    # run_command('pwd')
    # run_command(f'cd {tmpdir}')
    # run_command('pwd')
    # cmd = f"cp setup_project.sh {tmpdir}/setup_project.sh"
    # run_command(cmd)

    # # # cmd = f"cd {tmpdir} && chmod +x setup_project.sh"
    # # # run_command(cmd)

    # cmd = f"cd {tmpdir} && sh setup_project.sh"
    # run_command(cmd)

    # cmd = f"cd {tmpdir} && touch helloooooo.txt"
    # run_command(cmd)

    # # cmd = 'sh setup_project.sh'
    # # run_command(cmd)

    source_directory = Path(__file__).parent.parent / 'vendor'

    cmd = f'sh setup_project.sh -d {tmpdir} -s {source_directory}'
    run_command(cmd)

    print(tmpdir)
    assert 0