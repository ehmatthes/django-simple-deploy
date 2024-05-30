"""Unit tests for platform.sh utils."""

from pathlib import Path

import simple_deploy.management.commands.platform_sh.utils as plsh_utils


def test_get_project_name():
    path = Path(__file__).parent / "resources/projects_info_output_csv.txt"
    output_str = path.read_text()
    project_name = plsh_utils.get_project_name(output_str)

    assert project_name == "my_blog_project"


def test_get_org_names():
    """Make sure we get the org names, not label or email."""
    output_str = (
        "Name,Label,Owner email\nusername-name,username-label,username@example.com"
    )
    org_names = plsh_utils.get_org_names(output_str)
    assert org_names == ["username-name"]

    output_str = """Name,Label,Owner email
org_name,org_label,org_owner@example.com
org_name_2,org_label_2,org_owner_2@example.com"""

    org_names = plsh_utils.get_org_names(output_str)
    assert org_names == ["org_name", "org_name_2"]