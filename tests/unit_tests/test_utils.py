"""Tests for simple_deploy/management/commands/utils.py.

Note: May need to rethink handling of sd_config, if tests start to affect each other.
"""

from pathlib import Path
import filecmp
import sys
import subprocess

from simple_deploy.management.commands.utils import sd_utils
from simple_deploy.management.commands.utils import plugin_utils
from simple_deploy.management.commands.utils.plugin_utils import sd_config
from simple_deploy.management.commands.utils.command_errors import SimpleDeployCommandError

import pytest


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


# --- Parsing --platform arg ---

def test_get_plugin_name_default_plugins():
    """Test that the appropriate plugin name is determined from the --platform arg."""
    available_packages = ["django", "django-bootstrap5", "dsd_flyio", "dsd_platformsh", "dsd_heroku"]

    platform_arg = "fly_io"
    plugin_name = sd_utils._get_plugin_name_from_packages(platform_arg, available_packages)
    assert plugin_name == "dsd_flyio"

    platform_arg = "platform_sh"
    plugin_name = sd_utils._get_plugin_name_from_packages(platform_arg, available_packages)
    assert plugin_name == "dsd_platformsh"

    platform_arg = "heroku"
    plugin_name = sd_utils._get_plugin_name_from_packages(platform_arg, available_packages)
    assert plugin_name == "dsd_heroku"

def test_get_plugin_name_third_party_overlapping_plugin():
    """Test that appropriate plugin name returned for third-party plugin that overlaps default plugins."""
    available_packages = ["dsd_flyio_thirdparty", "django", "django-bootstrap5", "dsd_flyio", "dsd_platformsh", "dsd_heroku"]

    platform_arg = "fly_io"
    plugin_name = sd_utils._get_plugin_name_from_packages(platform_arg, available_packages)
    assert plugin_name == "dsd_flyio_thirdparty"

def test_get_plugin_name_third_party_non_overlapping_plugin():
    """Test that appropriate plugin name is returned when no overlap with defaults."""
    available_packages = ["dsd_nonoverlappingplatform", "django", "django-bootstrap5", "dsd_flyio", "dsd_platformsh", "dsd_heroku"]

    platform_arg = "nonoverlapping_platform"
    plugin_name = sd_utils._get_plugin_name_from_packages(platform_arg, available_packages)
    assert plugin_name == "dsd_nonoverlappingplatform"

def test_get_plugin_name_unavailable_plugin():
    """Test that exception raised when unavailable plugin requested."""
    available_packages = ["django", "django-bootstrap5", "dsd_flyio", "dsd_platformsh", "dsd_heroku"]

    platform_arg = "unsupported_platform"
    with pytest.raises(SimpleDeployCommandError):
        plugin_name = sd_utils._get_plugin_name_from_packages(platform_arg, available_packages)


# --- Parsing requirements ---


def test_parse_req_txt():
    path = Path(__file__).parent / "resources" / "requirements.txt"
    requirements = sd_utils.parse_req_txt(path)

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
    requirements = sd_utils.parse_pipfile(path)

    packages = ["django", "django-bootstrap5", "requests"]
    assert all([pkg in requirements for pkg in packages])


def test_parse_pyproject_toml():
    path = Path(__file__).parent / "resources" / "pyproject.toml"
    requirements = sd_utils.parse_pyproject_toml(path)

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
    assert filecmp.cmp(tmp_pptoml, ref_file)


def test_add_req_txt_pkg(tmp_path):
    path = Path(__file__).parent / "resources" / "requirements.txt"
    contents = path.read_text()

    # Create tmp copy of file, and modify that one.
    tmp_req_txt = tmp_path / "tmp_requirements.txt"
    tmp_req_txt.write_text(contents)

    plugin_utils.add_req_txt_pkg(tmp_req_txt, "awesome-deployment-package", "")
    ref_file = Path(__file__).parent / "reference_files" / "requirements.txt"
    assert filecmp.cmp(tmp_req_txt, ref_file)


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
    assert filecmp.cmp(tmp_pptoml, ref_file)


def test_add_pipenv_pkg(tmp_path):
    path = Path(__file__).parent / "resources" / "Pipfile"
    contents = path.read_text()

    # Create tmp copy of file, and modify that one.
    tmp_pipfile = tmp_path / "tmp_pipfile"
    tmp_pipfile.write_text(contents)

    plugin_utils.add_pipenv_pkg(tmp_pipfile, "awesome-deployment-package", "")
    ref_file = Path(__file__).parent / "reference_files" / "Pipfile"
    assert filecmp.cmp(tmp_pipfile, ref_file)


# --- Tests for functions that require sd_config ---


def test_add_file(tmp_path):
    """Test utility for adding a file."""
    sd_config.unit_testing = "True"
    sd_config.stdout = sys.stdout

    contents = "Sample file contents.\n"
    path = tmp_path / "test_add_file.txt"
    assert not path.exists()

    plugin_utils.add_file(path, contents)
    assert path.exists()

    contents_from_file = path.read_text()
    assert contents_from_file == contents
