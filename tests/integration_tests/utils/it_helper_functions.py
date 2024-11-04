"""Helper functions for integration tests of different platforms.

The functions in this module are not specific to any one platform. If a function
  starts to be used by integration tests for more than one platform, it should be moved here.
"""

from pathlib import Path
import filecmp
import re
import shutil
import sys
import subprocess
from textwrap import dedent

import pytest


def check_reference_file(tmp_proj_dir, filepath, plugin_name="", reference_filename=""):
    """Check that the test version of the file matches the reference version
    of the file.

    - filepath: relative path from tmp_proj_dir to test file
    - reference_filename: the name of the  reference file, if it has a
      different name than the generated file

    Asserts:
    - Asserts that the file at `filepath` matches the reference file of the
      same name, or the specific reference file given.

    Returns:
    - None
    """

    # Path to the generated file is exactly as given, from tmp_proj_dir.
    fp_generated = tmp_proj_dir / filepath
    assert fp_generated.exists()

    # There are no subdirectories in references/, so we only need to keep
    #   the actual filename.
    # For example if filepath is `blog/settings.py`, we only want `settings.py`.
    if reference_filename:
        filename = Path(reference_filename)
    else:
        filename = Path(filepath).name

    # Root directory of local simple_deploy project.
    sd_root_dir = Path(__file__).parents[3]
    print("sd_root_dir:", sd_root_dir)

    # Only plugins use reference files for now. Assume plugin dir is in same directory as
    # django-simple-deploy.
    if plugin_name:
        plugin_root_dir = sd_root_dir.parent / plugin_name
        assert plugin_root_dir.exists()
        
        fp_reference = plugin_root_dir / f"tests/integration_tests/reference_files/{filename}"
        assert fp_reference.exists()

    # The test file and reference file will always have different modified
    #   timestamps, so no need to use default shallow=True.
    assert filecmp.cmp(fp_generated, fp_reference, shallow=False)


def check_package_manager_available(pkg_manager):
    """Check that the user has required package managers installed before
    running integration tests. For example, we need Poetry installed in order to
    test configuration when the end user uses Poetry for their Django projects.
    """

    # Check that the package manager is installed by calling `which`; I believe
    #   shutil then calls `where` on Windows.
    pkg_manager_path = shutil.which(pkg_manager)

    # If they have it installed, continue with testing. Otherwise, let them know
    #   how to install the given package manager.
    if pkg_manager_path:
        return True
    else:
        msg = dedent(
            f"""
        --- You must have {pkg_manager.title()} installed in order to run integration tests. ---

        If you have a strong reason not to install {pkg_manager.title()}, please open an issue
        and share your reasoning. We can look at installing {pkg_manager.title()} to the test
        environment each time a test is run.

        Instructions for installing {pkg_manager.title()} can be found here:
        """
        )

        if pkg_manager == "poetry":
            msg += "https://python-poetry.org/docs/#installation"
        elif pkg_manager == "pipenv":
            msg += "https://pipenv.pypa.io/en/latest/install/#installing-pipenv"

        pytest.exit(msg)

