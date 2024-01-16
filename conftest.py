"""Root conftest.py"""

import os
import sys
from pathlib import Path

import pytest


# def check_valid_test_call():
#     """Ensure either e2e tests, or local tests are being run, but not both.

#     Unit tests and integration tests make no network calls; they can be run together,
#     and they are run with a bare `pytest` call.

#     e2e tests are much slower, and create resources that can accrue charges. Running e2e
#     tests requires an explicit call.

#     Returns: True or False
#     """
#     # Running from specific directories is appropriate.
#     if Path.cwd().name in ('unit_tests_real', 'unit_tests', 'e2e_tests'):
#         return True

#     # If e2e tests are being requested, make sure others are not.


#     # Find out what kind of tests are being requested.
#     unit_testing = any('unit_tests' in arg for arg in sys.argv)
#     e2e_testing = any('e2e_tests' in arg for arg in sys.argv)

#     # Allow one kind of testing.
#     if [unit_testing, e2e_testing].count(True) == 1:
#         return True

#     # If we don't recognize the test command as valid or invalid, assume invalid.
#     return False


# if not check_valid_test_call():
#     msg = "You must run either local tests or e2e tests, not both."
#     msg += "\n  Either specify the tests you want to run, or cd"
#     msg += "\n  into the appropriate directory and run tests from there."
#     print(msg)

#     sys.exit()

# def pytest_collection_modifyitems(session, config, items):
    
#     print("--- Removing sample project tests ---")
#     print(len(items))
#     items[:] = [i for i in items if "sample_project/" not in str(i.fspath)]
#     print(len(items))

#     print("--- end diagnostics ---")

# Don't look at any test files in the sample_project/ dir.
collect_ignore = ["sample_project"]