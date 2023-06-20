"""Configuration for integration tests."""

import sys

def check_valid_call():
    """Make sure the test call works for integration tests."""
    # Require -s flag.
    # This is required for some prompts. Also, integration testing involves a full
    #   deployment, and there's information generated that really needs to be in
    #   the test output at this point.
    if '-s' not in sys.argv:
        msg = "You must use the `-s` flag when running integration tests."
        print(msg)
        return False

    # Verify that a specific platform has been requested.
    if any(platform in ' '.join(sys.argv) for platform in ['platform_sh', 'fly_io', 'heroku']):
        return True
    else:
        msg = "For integration testing, you must target a specific platform."
        print(msg)
        return False

    # Can't verify it was a valid call, so return False.
    return False

if not check_valid_call():
    print("That is not a valid command for integration testing.")
    sys.exit()