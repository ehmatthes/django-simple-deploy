"""Root conftest.py"""

import os
import sys
from pathlib import Path

import pytest


# Only run pytest from unit_tests/.
#   If it makes sense to call pytest at the project root, overwrite this file.
if Path.cwd().name != "unit_tests":
    print("To run unit tests, first cd into the unit_tests/ directory, and then run pytest.")
    sys.exit()