"""Tests for simple_deploy/management/commands/utils.py."""

import django
import simple_deploy.management.commands.utils as sd_utils

def test_strip_secret_key_with_key():
    line = "SECRET_KEY = 'django-insecure-j+*1=he4!%=(-3g^$hj=1pkmzkbdjm0-h2%yd-=1sf%trwun_-'"
    stripped_line = sd_utils.strip_secret_key(line)
    assert stripped_line == "SECRET_KEY = *value hidden*"

def test_strip_secret_key_without_key():
    line = "INSTALLED_APPS = ["
    stripped_line = sd_utils.strip_secret_key(line)
    assert stripped_line == line