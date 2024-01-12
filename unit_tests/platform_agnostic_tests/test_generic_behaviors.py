"""Test behaviors that depend on a full run, but aren't specific to a platform.

Should be able to use any valid platform for these calls.
"""

from pathlib import Path
import subprocess, shlex, os, sys

import pytest

from ..utils import manage_sample_project as msp


# --- Fixtures ---


# --- Helper functions ---


# --- Tests without --ignore-unclean-git flag. ---