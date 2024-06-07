"""Test utility functions for examining git status."""

from textwrap import dedent

import simple_deploy.management.commands.utils as sd_utils

import pytest


# --- Tests for checking git status ---


def test_simple_git_status():
    """Tests for simple `git status --porcelain` and `git diff --unified=0` outputs."""
    status_output, diff_output = "", ""
    assert sd_utils.check_status_output(status_output, diff_output)

    status_output, diff_output = " M .gitignore", ""
    assert sd_utils.check_status_output(status_output, diff_output)

    status_output, diff_output = " M settings.py", ""
    assert sd_utils.check_status_output(status_output, diff_output)

    status_output, diff_output = " M .gitignore\n M settings.py", ""
    assert sd_utils.check_status_output(status_output, diff_output)

    status_output, diff_output = " M blog/settings.py\n?? simple_deploy_logs/", ""
    assert sd_utils.check_status_output(status_output, diff_output)


# --- Tests for checking overall git diff ---


def test_diff_ignore_sd_logs():
    diff_output = dedent(
        """\
        diff --git a/.gitignore b/.gitignore
        index 9c96d1b..4279ffb 100644
        --- a/.gitignore
        +++ b/.gitignore
        @@ -8,0 +9,3 @@ db.sqlite3
        +
        +simple_deploy_logs/"""
    )

    assert sd_utils._check_git_diff(diff_output)


def test_diff_settings_sd_installed_apps():
    diff_output = dedent(
        """\
        diff --git a/blog/settings.py b/blog/settings.py
        index 6d40136..6395c5a 100644
        --- a/blog/settings.py
        +++ b/blog/settings.py
        @@ -39,0 +40 @@ INSTALLED_APPS = [
        +    'simple_deploy',
        @@ -134 +135 @@ DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'"""
    )

    assert sd_utils._check_git_diff(diff_output)


def test_diff_settings_requirements_txt():
    diff_output = dedent(
        """\
        diff --git a/.gitignore b/.gitignore
        index 9c96d1b..95a2c40 100644
        --- a/.gitignore
        +++ b/.gitignore
        @@ -8,0 +9,2 @@ db.sqlite3
        +
        +simple_deploy_logs/
        diff --git a/requirements.txt b/requirements.txt
        index b121799..b28fb7a 100644
        --- a/requirements.txt
        +++ b/requirements.txt
        @@ -9,0 +10,2 @@ urllib3==1.26.12
        +
        +django-simple-deploy
        \\ No newline at end of file"""
    )

    assert sd_utils._check_git_diff(diff_output)


def test_diff_unacceptable_change():
    diff_output = dedent(
        """\
        diff --git a/blog/settings.py b/blog/settings.py
        index 47b3c94..2ef71ca 100644
        --- a/blog/settings.py
        +++ b/blog/settings.py
        @@ -135 +135,2 @@ DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'
        -LOGIN_URL = 'users:login'
        \\ No newline at end of file
        +LOGIN_URL = 'users:login'
        +# Placeholder comment to create unacceptable git status."""
    )

    assert not sd_utils._check_git_diff(diff_output)


def test_diff_sdlogs_gitignore_sd_installed_apps():
    diff_output = dedent(
        """\
        diff --git a/.gitignore b/.gitignore
        index 9c96d1b..95a2c40 100644
        --- a/.gitignore
        +++ b/.gitignore
        @@ -8,0 +9,2 @@ db.sqlite3
        +
        +simple_deploy_logs/
        diff --git a/blog/settings.py b/blog/settings.py
        index 6d40136..77a88d2 100644
        --- a/blog/settings.py
        +++ b/blog/settings.py
        @@ -39,0 +40 @@ INSTALLED_APPS = [
        +    'simple_deploy',"""
    )

    assert sd_utils._check_git_diff(diff_output)


# --- Tests for _clean_diff(); also includes test of checking the clean diff ---


def test_clean_diff():
    diff_output = dedent(
        """\
        diff --git a/blog/settings.py b/blog/settings.py
        index 6d40136..6395c5a 100644
        --- a/blog/settings.py
        +++ b/blog/settings.py
        @@ -39,0 +40 @@ INSTALLED_APPS = [
        +    'simple_deploy',
        @@ -134 +135 @@ DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'"""
    )

    cleaned_diff = sd_utils._clean_diff(diff_output.splitlines())
    assert cleaned_diff == ["+    'simple_deploy',"]
    assert sd_utils._check_settings_diff(diff_output.splitlines())


def test_clean_diff_remove_blank_changes():
    diff_output = dedent(
        """\
        diff --git a/blog/settings.py b/blog/settings.py
        index 47b3c94..aed7c56 100644
        --- a/blog/settings.py
        +++ b/blog/settings.py
        @@ -135 +135,4 @@ DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'
        +
        +# Placeholder comment to create unacceptable git status.
        +"""
    )

    cleaned_diff = sd_utils._clean_diff(diff_output.splitlines())
    assert cleaned_diff == ["+# Placeholder comment to create unacceptable git status."]
    assert not sd_utils._check_settings_diff(diff_output.splitlines())


def test_clean_diff_remove_trailing_newline():
    diff_output = dedent(
        """\
        diff --git a/blog/settings.py b/blog/settings.py
        index 47b3c94..aed7c56 100644
        --- a/blog/settings.py
        +++ b/blog/settings.py
        @@ -135 +135,4 @@ DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'
        +
        +# Placeholder comment to create unacceptable git status.
        +\n"""
    )

    cleaned_diff = sd_utils._clean_diff(diff_output.splitlines())
    assert cleaned_diff == ["+# Placeholder comment to create unacceptable git status."]
    assert not sd_utils._check_settings_diff(diff_output.splitlines())


def test_clean_diff_gitignore():
    diff_output = dedent(
        """\
        diff --git a/.gitignore b/.gitignore
        index 9c96d1b..95a2c40 100644
        --- a/.gitignore
        +++ b/.gitignore
        @@ -8,0 +9,2 @@ db.sqlite3
        +
        +simple_deploy_logs/"""
    )

    cleaned_diff = sd_utils._clean_diff(diff_output.splitlines())
    assert cleaned_diff == ["+simple_deploy_logs/"]
    assert sd_utils._check_gitignore_diff(diff_output.splitlines())


def test_clean_diff_settings():
    diff_output = dedent(
        """\
        diff --git a/blog/settings.py b/blog/settings.py
        index 6d40136..77a88d2 100644
        --- a/blog/settings.py
        +++ b/blog/settings.py
        @@ -39,0 +40 @@ INSTALLED_APPS = [
        +    'simple_deploy',"""
    )

    cleaned_diff = sd_utils._clean_diff(diff_output.splitlines())
    assert cleaned_diff == ["+    'simple_deploy',"]
    assert sd_utils._check_settings_diff(diff_output.splitlines())
