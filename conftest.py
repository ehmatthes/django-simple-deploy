"""Root conftest.py"""

import os
import sys
from pathlib import Path

import pytest


def check_valid_test_call():
    """When testing, you must specify either unit_tests or integration_tests.
    It doesn't make sense to run both kinds of tests in the same test run.

    Returns: True or False
    """
    # Running from either unit_tests/ or integration_tests/ is fine.
    if Path.cwd().name in ('unit_tests', 'integration_tests'):
        return True

    # Find out what kind of tests are being requested.
    unit_testing = any('unit_tests' in arg for arg in sys.argv)
    integration_testing = any('integration_tests' in arg for arg in sys.argv)

    # Allow one kind of testing.
    if [unit_testing, integration_testing].count(True) == 1:
        return True

    # If we don't recognize the test command as valid or invalid, assume invalid.
    return False


if not check_valid_test_call():
    msg = "You must run either unit tests or integration tests, not both."
    msg += "\n  Either specify the tests you want to run, or cd"
    msg += "\n  into the appropriate directory and run tests from there."
    print(msg)

    sys.exit()