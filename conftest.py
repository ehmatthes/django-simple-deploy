"""Root conftest.py"""

import sys
from pathlib import Path

import pytest

# Let plugins import utilities.
path = Path(__file__).parent / "tests" / "integration_tests" / "utils"
sys.path.insert(0, path)


# Don't look at any test files in the sample_project/ dir.
collect_ignore = ["sample_project"]


# If not running e2e tests, ignore entire e2e_tests directory.
# DEV: Most of this will be removed when plugins are external.
running_e2e = any(["e2e_tests" in arg for arg in sys.argv])
if not running_e2e:
    collect_ignore.append("tests/e2e_tests")
    for platform in ["fly_io", "platform_sh", "heroku"]:
        collect_ignore.append(
            f"simple_deploy/management/commands/{platform}/tests/e2e_tests"
        )
