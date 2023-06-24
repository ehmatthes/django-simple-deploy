"""Helper functions for integration tests of different platforms.

The functions in this module are not specific to any one platform. If a function
  starts to be used by tests for more than one platform, it should be moved here.
"""

import subprocess, shlex


def make_sp_call(cmd, capture_output=False):
    """Make a subprocess call.

    This wrapper function lets test code use full commands, rather than
      lists of command parts. This makes it much easier to follow what testing
      code is doing.

    Returns: None, or CompletedProcess instance.
    """
    cmd_parts = shlex.split(cmd)

    return subprocess.run(cmd_parts, capture_output=capture_output)