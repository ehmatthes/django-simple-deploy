"""Tests for simple_deploy/management/commands/utils.py."""

from pathlib import Path

import django
import simple_deploy.management.commands.utils as sd_utils
import simple_deploy.management.commands.simple_deploy as sd
import subprocess


def test_strip_secret_key_with_key():
    line = "SECRET_KEY = 'django-insecure-j+*1=he4!%=(-3g^$hj=1pkmzkbdjm0-h2%yd-=1sf%trwun_-'"
    stripped_line = sd_utils.strip_secret_key(line)
    assert stripped_line == "SECRET_KEY = *value hidden*"


def test_strip_secret_key_without_key():
    line = "INSTALLED_APPS = ["
    assert sd_utils.strip_secret_key(line) == line


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


def test_parse_req_txt():
    path = Path(__file__).parent / "resources" / "requirements.txt"
    requirements = sd_utils.parse_req_txt(path)
    print("\n", requirements)

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
