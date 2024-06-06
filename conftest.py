"""Root conftest.py"""

import sys
from pathlib import Path

import pytest

# Let plugins import utilities.
path = Path(__file__).parent / "tests" / "integration_tests" / "utils"
sys.path.insert(0, path)


# Don't look at any test files in the sample_project/ dir.
collect_ignore = ["sample_project"]

# If not running an e2e test, completely ignore those tests.
# DEV: This block should be removed after moving all e2e tests to plugins.
# if "e2e_tests" not in sys.argv:
#     collect_ignore.append("tests/e2e_tests")


# # # If running a plugin's e2e tests, run the e2e_tests conftest?
# # running_e2e = any(["e2e_tests" in arg for arg in sys.argv])
# # if running_e2e:
# #     import tests.e2e_tests.conftest as e2e_conftest

# #     def pytest_configure(config):
# #         if not e2e_conftest.check_valid_call(config):
# #             pytest.exit("Invalid command for e2e testing.")

# # If running a plugin's e2e tests, run the e2e_tests conftest?
# import importlib
# def pytest_configure(config):
#     running_e2e = any(["e2e_tests" in arg for arg in sys.argv])
#     if not running_e2e:
#         return

#     import tests.e2e_tests.conftest as e2e_conftest

#     if not e2e_conftest.check_valid_call(config):
#         pytest.exit("Invalid command for e2e testing.")
    
#     def pytest_addoption(parser):
#         e2e_conftest.pytest_addoption(parser)






running_e2e = any(["e2e_tests" in arg for arg in sys.argv])

# if not running_e2e:
#     collect_ignore.append("tests/e2e_tests/platforms")
# else:
#     # Run a dummy test in tests/e2e_tests, to force evaluation of e2e_tests/conftest.py?
#     ...


# # Always ignore platform e2e tests.
# collect_ignore.append("tests/e2e_tests/platforms")

# If not running e2e tests, ignore entire e2e_tests as well.
if not running_e2e:
    collect_ignore.append("tests/e2e_tests")
else:
    collect_ignore.append("tests/e2e_tests/platforms")