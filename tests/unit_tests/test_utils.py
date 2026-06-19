"""Tests for django_simple_deploy/management/commands/utils.py.

Note: May need to rethink handling of dsd_config, if tests start to affect each other.
"""

from pathlib import Path
import filecmp
import sys
import subprocess

from django_simple_deploy.management.commands.utils import dsd_utils
from django_simple_deploy.management.commands.utils import plugin_utils
from django_simple_deploy.management.commands.utils.plugin_utils import dsd_config
from django_simple_deploy.management.commands.utils.command_errors import (
    DSDCommandError,
)

import pytest


def compare_text_files (path1, path2):
    """Compares two text files, ignoring differences in line terminators

    If a text file is written under Unix and Windows, line terminators
    will be different (LF vs. CRLF) even if the contents are otherwise
    identical. Function filecmp.cmp() considers both versions of the
    file different. But sometimes it may be desirable to consider them equal.

    - path1: first file to compare
    - path2: second file to compare

    Returns:
        - True if file contents are identical except for possible
          differences in line terminators
        - False otherwise
    """
    lines1 = path1.read_text().splitlines()
    lines2 = path2.read_text().splitlines()

    if len (lines1) != len (lines2):
        return False
    
    for (l1, l2) in zip (lines1, lines2):
        if l1 != l2:
            return False
        
    return True


# --- Fixtures ---


# --- Test functions ---


def test_strip_secret_key_with_key():
    line = "SECRET_KEY = 'django-insecure-j+*1=he4!%=(-3g^$hj=1pkmzkbdjm0-h2%yd-=1sf%trwun_-'"
    stripped_line = plugin_utils._strip_secret_key(line)
    assert stripped_line == "SECRET_KEY = *value hidden*"


def test_strip_secret_key_without_key():
    line = "INSTALLED_APPS = ["
    assert plugin_utils._strip_secret_key(line) == line


def test_get_string_from_output_string():
    output = "Please select a platform:"
    assert plugin_utils.get_string_from_output(output) == output


def test_get_string_from_output_with_stdout():
    output_obj = subprocess.CompletedProcess(
        args=[], returncode=0, stdout=b"Hello World\n", stderr=b""
    )
    assert plugin_utils.get_string_from_output(output_obj) == "Hello World\n"


def test_get_string_from_output_with_stderr():
    output_obj = subprocess.CompletedProcess(
        args=[], returncode=1, stdout=b"", stderr=b"Error message\n"
    )
    assert plugin_utils.get_string_from_output(output_obj) == "Error message\n"


# --- Parsing plugin names ---


def test_get_plugin_name_default_plugins():
    """Test that the appropriate plugin name is determined when an official plugin is installed."""
    available_packages = [
        "django",
        "django-bootstrap5",
        "dsd_flyio",
    ]

    plugin_name = dsd_utils._get_plugin_name_from_packages(available_packages)
    assert plugin_name == "dsd_flyio"


def test_get_plugin_name_third_party_plugin():
    """Test that appropriate plugin name returned for third-party plugin."""
    available_packages = [
        "dsd_flyio_thirdparty",
        "django",
        "django-bootstrap5",
    ]

    plugin_name = dsd_utils._get_plugin_name_from_packages(available_packages)
    assert plugin_name == "dsd_flyio_thirdparty"


def test_get_plugin_name_no_plugins():
    """Test that exception raised when no plugins installed."""
    available_packages = [
        "django",
        "django-bootstrap5",
    ]

    with pytest.raises(DSDCommandError):
        plugin_name = dsd_utils._get_plugin_name_from_packages(available_packages)


def test_get_plugin_name_too_many_plugins():
    """Test that having more than one plugin installed raises an exception.

    DEV: This needs to be rewritten when that case is handled by lettting user select plugin to use.
    """
    available_packages = [
        "dsd_newplatform",
        "dsd_newplatform_high_scale",
        "dsd_flyio",
        "django",
        "django-bootstrap5",
    ]

    with pytest.raises(DSDCommandError):
        plugin_name = dsd_utils._get_plugin_name_from_packages(available_packages)


# --- Parsing requirements ---


def test_parse_req_txt():
    path = Path(__file__).parent / "resources" / "requirements.txt"
    requirements = dsd_utils.parse_req_txt(path)

    assert requirements == [
        "asgiref",
        "certifi",
        "charset-normalizer",
        "Django",
        "django-bootstrap5",
        "idna",
        "requests",
        "sqlparse",
        "urllib3",
        "matplotlib",
        "plotly",
    ]


def test_parse_pipfile():
    path = Path(__file__).parent / "resources" / "Pipfile"
    requirements = dsd_utils.parse_pipfile(path)

    packages = ["django", "django-bootstrap5", "requests"]
    assert all([pkg in requirements for pkg in packages])


def test_parse_pyproject_toml():
    path = Path(__file__).parent / "resources" / "pyproject.toml"
    requirements = dsd_utils.parse_pyproject_toml(path)

    assert requirements == [
        "Django",
        "django-bootstrap5",
        "requests",
    ]


def test_create_poetry_deploy_group(tmp_path):
    path = Path(__file__).parent / "resources" / "pyproject_no_deploy.toml"
    contents = path.read_text()

    # Create tmp copy of file, and modify that one.
    tmp_pptoml = tmp_path / "pp.toml"
    tmp_pptoml.write_text(contents)

    plugin_utils.create_poetry_deploy_group(tmp_pptoml)
    ref_file = Path(__file__).parent / "reference_files" / "pyproject.toml"
    assert compare_text_files(tmp_pptoml, ref_file)


def test_add_req_txt_pkg(tmp_path):
    path = Path(__file__).parent / "resources" / "requirements.txt"
    contents = path.read_text()

    # Create tmp copy of file, and modify that one.
    tmp_req_txt = tmp_path / "tmp_requirements.txt"
    tmp_req_txt.write_text(contents)

    plugin_utils.add_req_txt_pkg(tmp_req_txt, "awesome-deployment-package", "")
    ref_file = Path(__file__).parent / "reference_files" / "requirements.txt"
    assert compare_text_files(tmp_req_txt, ref_file)


def test_add_poetry_pkg(tmp_path):
    path = (
        Path(__file__).parent / "resources" / "pyproject_toml_empty_deploy_group.toml"
    )
    contents = path.read_text()

    # Create tmp copy of file, and modify that one.
    tmp_pptoml = tmp_path / "pp.toml"
    tmp_pptoml.write_text(contents)

    plugin_utils.add_poetry_pkg(tmp_pptoml, "awesome-deployment-package", "")
    ref_file = (
        Path(__file__).parent
        / "reference_files"
        / "pyproject_deploy_group_awesome_pkg.toml"
    )
    assert compare_text_files(tmp_pptoml, ref_file)


def test_add_pipenv_pkg(tmp_path):
    path = Path(__file__).parent / "resources" / "Pipfile"
    contents = path.read_text()

    # Create tmp copy of file, and modify that one.
    tmp_pipfile = tmp_path / "tmp_pipfile"
    tmp_pipfile.write_text(contents)

    plugin_utils.add_pipenv_pkg(tmp_pipfile, "awesome-deployment-package", "")
    ref_file = Path(__file__).parent / "reference_files" / "Pipfile"
    assert compare_text_files(tmp_pipfile, ref_file)


# --- Tests for functions that require dsd_config ---


def test_add_file(tmp_path):
    """Test utility for adding a file."""
    dsd_config.unit_testing = "True"
    dsd_config.stdout = sys.stdout

    contents = "Sample file contents.\n"
    path = tmp_path / "test_add_file.txt"
    assert not path.exists()

    plugin_utils.add_file(path, contents)
    assert path.exists()

    contents_from_file = path.read_text()
    assert contents_from_file == contents
