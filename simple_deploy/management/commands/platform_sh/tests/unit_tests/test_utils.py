"""Unit tests for platform.sh utils."""

from pathlib import Path

import simple_deploy.management.commands.platform_sh.utils as plsh_utils


def test_get_project_name():
    path = Path(__file__).parent / "resources/projects_info_output_csv.txt"
    output_str = path.read_text()
    project_name = plsh_utils.get_project_name(output_str)

    assert project_name == "my_blog_project"

