"""Test utility functions for examining git status."""

from textwrap import dedent

import simple_deploy.management.commands.utils as sd_utils

import pytest


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


def test_diff_settings_sd_with_newline():
    """Make sure a newline change at end of file doesn't fail the git status check."""
    diff_output = dedent(
        """\
        diff --git a/blog/settings.py b/blog/settings.py
        index 6d40136..6395c5a 100644
        --- a/blog/settings.py
        +++ b/blog/settings.py
        @@ -39,0 +40 @@ INSTALLED_APPS = [
        +    'simple_deploy',
        @@ -134 +135 @@ DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'
        -LOGIN_URL = 'users:login'
        \\ No newline at end of file
        +LOGIN_URL = 'users:login'"""
    )

    assert sd_utils._check_git_diff(diff_output)

def test_clean_diff():
    diff_output = dedent(
        """\
        diff --git a/blog/settings.py b/blog/settings.py
        index 6d40136..6395c5a 100644
        --- a/blog/settings.py
        +++ b/blog/settings.py
        @@ -39,0 +40 @@ INSTALLED_APPS = [
        +    'simple_deploy',
        @@ -134 +135 @@ DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'
        -LOGIN_URL = 'users:login'
        \\ No newline at end of file
        +LOGIN_URL = 'users:login'"""
    )

    cleaned_diff = sd_utils._clean_diff(diff_output.splitlines())
    assert cleaned_diff == ["+    'simple_deploy',"]