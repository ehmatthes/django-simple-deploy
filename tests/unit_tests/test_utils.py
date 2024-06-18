"""Tests for simple_deploy/management/commands/utils.py."""

from pathlib import Path
import filecmp

import simple_deploy.management.commands.utils as sd_utils
import subprocess

import pytest


def test_strip_secret_key_with_key():
    line = "SECRET_KEY = 'django-insecure-j+*1=he4!%=(-3g^$hj=1pkmzkbdjm0-h2%yd-=1sf%trwun_-'"
    stripped_line = sd_utils._strip_secret_key(line)
    assert stripped_line == "SECRET_KEY = *value hidden*"


def test_strip_secret_key_without_key():
    line = "INSTALLED_APPS = ["
    assert sd_utils._strip_secret_key(line) == line


def test_get_string_from_output_string():
    output = "Please select a platform:"
    assert sd_utils.get_string_from_output(output) == output


def test_get_string_from_output_with_stdout():
    output_obj = subprocess.CompletedProcess(
        args=[], returncode=0, stdout=b"Hello World\n", stderr=b""
    )
    assert sd_utils.get_string_from_output(output_obj) == "Hello World\n"


def test_get_string_from_output_with_stderr():
    output_obj = subprocess.CompletedProcess(
        args=[], returncode=1, stdout=b"", stderr=b"Error message\n"
    )
    assert sd_utils.get_string_from_output(output_obj) == "Error message\n"


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

    sd_utils.create_poetry_deploy_group(tmp_pptoml)
    ref_file = Path(__file__).parent / "reference_files" / "pyproject.toml"
    assert filecmp.cmp(tmp_pptoml, ref_file)


def test_add_req_txt_pkg(tmp_path):
    path = Path(__file__).parent / "resources" / "requirements.txt"
    contents = path.read_text()

    # Create tmp copy of file, and modify that one.
    tmp_req_txt = tmp_path / "tmp_requirements.txt"
    tmp_req_txt.write_text(contents)

    sd_utils.add_req_txt_pkg(tmp_req_txt, "awesome-deployment-package", "")
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

    sd_utils.add_poetry_pkg(tmp_pptoml, "awesome-deployment-package", "")
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

    sd_utils.add_pipenv_pkg(tmp_pipfile, "awesome-deployment-package", "")
    ref_file = Path(__file__).parent / "reference_files" / "Pipfile"
    assert filecmp.cmp(tmp_pipfile, ref_file)
