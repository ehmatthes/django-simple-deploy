"""Tests for simple_deploy/management/commands/utils.py."""

from pathlib import Path

import django
import simple_deploy.management.commands.utils as sd_utils
import simple_deploy.management.commands.simple_deploy as sd
import subprocess

import pytest


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


# --- git status checks ---

@pytest.mark.skip()
def test_simple_git_status():
    """Tests for simple `git status --porcelain` and `git diff --unified=0` outputs."""
    status_output = " M .gitignore"
    diff_output = ""
    assert sd_utils.check_status_output(status_output, diff_output)

    status_output = " M .gitignore"
    diff_output = "diff --git a/.gitignore b/.gitignore\nindex 9c96d1b..4279ffb 100644\n--- a/.gitignore\n+++ b/.gitignore\n@@ -8,0 +9,3 @@ db.sqlite3\n+\n+# Ignore logs from simple_deploy.\n+simple_deploy_logs/"
    assert sd_utils.check_status_output(status_output, diff_output)

    status_output = " M blog/settings.py\n?? simple_deploy_logs/"
    diff_output = "diff --git a/blog/settings.py b/blog/settings.py\nindex 6d40136..6395c5a 100644\n--- a/blog/settings.py\n+++ b/blog/settings.py\n@@ -39,0 +40 @@ INSTALLED_APPS = [\n+    'simple_deploy',\n@@ -134 +135 @@ DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'\n-LOGIN_URL = 'users:login'\n\\ No newline at end of file\n+LOGIN_URL = 'users:login'"
    assert sd_utils.check_status_output(status_output, diff_output)


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

    assert requirements == [
        "django",
        "django-bootstrap5",
        "requests",
    ]


def test_parse_pyproject_toml():
    path = Path(__file__).parent / "resources" / "pyproject.toml"
    requirements = sd_utils.parse_pyproject_toml(path)

    assert requirements == [
        "Django",
        "django-bootstrap5",
        "requests",
    ]
