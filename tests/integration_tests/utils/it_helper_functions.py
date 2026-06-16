"""Helper functions for integration tests of different platforms.

The functions in this module are not specific to any one platform. If a function
  starts to be used by integration tests for more than one platform, it should be moved here.
"""

from pathlib import Path
import filecmp
import importlib
import re
import shutil
import sys
import subprocess
from textwrap import dedent

import pytest

from django_simple_deploy.management.commands.utils import dsd_utils
from django_simple_deploy.management.commands.utils.command_errors import (
    DSDCommandError,
)
from ...unit_tests.test_utils import compare_text_files


def check_reference_file(
    tmp_proj_dir,
    filepath,
    plugin_name="",
    reference_filename="",
    reference_filepath=None,
    context=None,
    tmp_path=None,
):
    """Check that the test version of the file matches the reference version
    of the file.

    - filepath: relative path from tmp_proj_dir to test file
    - reference_filename: the name of the  reference file, if it has a
      different name than the generated file
    - reference_filepath: absolute path to reference file
    - plugin_name: used to find the path to reference files.
    - context: used to fill in placeholders in the reference file; reference file is not modified
    - tmp_path: If a context is provided, also provide a tmp path where the generated reference file
      can be stored. This approach means it will be a pytest-generated path, which can be found in a way
      that's consistent with other tmp files generated during testing.

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

    # Root directory of local django-simple-deploy project.
    sd_root_dir = Path(__file__).parents[3]
    print("sd_root_dir:", sd_root_dir)

    # Only plugins use reference files for now. Assume plugin dir is in same directory as
    # django-simple-deploy.
    if reference_filepath:
        fp_reference = reference_filepath
    elif plugin_name:
        plugin_root_dir = sd_root_dir.parent / plugin_name
        assert plugin_root_dir.exists()

        fp_reference = (
            plugin_root_dir / f"tests/integration_tests/reference_files/{filename}"
        )
        assert fp_reference.exists()

    # If caller has provided a context, use it to generate a temp reference file with placeholders
    # filled in.
    if context:
        contents = fp_reference.read_text()
        for placeholder, replacement in context.items():
            contents = contents.replace(f"{{{placeholder}}}", replacement)

        fp_reference = tmp_path / filename
        fp_reference.write_text(contents)

    # Compare files line by line, ignoring differences in line terminators
    assert compare_text_files(fp_generated, fp_reference)


def check_plugin_available(config):
    """If no plugin specified, make sure one is available."""
    if config.option.plugin:
        return

    # No plugin specified; make sure one is installed.
    try:
        dsd_utils.get_plugin_name()
    except DSDCommandError:
        msg = "\n*** No plugins installed. Skipping integration tests. ***"
        print(msg)
        pytest.skip()


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

        --- To run the full set of tests, {pkg_manager.title()} should be installed. ---
          Instructions for installing {pkg_manager.title()} can be found here:
        """
        )

        if pkg_manager == "poetry":
            msg += "  https://python-poetry.org/docs/#installation\n"
        elif pkg_manager == "pipenv":
            msg += "  https://pipenv.pypa.io/en/latest/install/#installing-pipenv\n"

        print(msg)

        return False
