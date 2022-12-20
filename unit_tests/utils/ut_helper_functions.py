"""Helper functions for unit tests of different platforms.

The functions in this module are not specific to any one platform. If a function
  starts to be used by unit tests for more than one platform, it should be moved here.
"""

from pathlib import Path
import filecmp

def check_reference_file(tmp_proj_dir, filepath, platform,
        reference_filename=""):
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

    # Root directory of local simple_deploy project.
    sd_root_dir = Path(__file__).parents[3]

    # Path to the generated file is exactly as given, from tmp_proj_dir.
    fp_generated = tmp_proj_dir / filepath

    # There are no subdirectories in references/, so we only need to keep
    #   the actual filename.
    # For example if filepath is `blog/settings.py`, we only want `settings.py`.
    if reference_filename:
        filename = Path(reference_filename)
    else:
        filename = Path(filepath).name
    fp_reference = Path(f'platforms/{platform}/reference_files/{filename}')

    # The test file and reference file will always have different modified
    #   timestamps, so no need to use default shallow=True.
    assert filecmp.cmp(fp_generated, fp_reference, shallow=False)