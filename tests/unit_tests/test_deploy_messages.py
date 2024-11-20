"""Tests for cross-platform deploy messages.

These functions simply return strings. However, it can be easy to forget a
return statement at the end of a dynamic function, and it can be easy to get 
inconsistent spacing in the messages that are returned.

A test here should mean that the spacing has been verified as appropriate in an actual
run of simple_deploy. For example make a run with automate_all, cancel the run, and make
sure the spacing of the rendered message looks appropriate.
"""

from simple_deploy.management.commands import sd_messages


# --- Static messages ---


# Just test one static message for now.
def test_cancel_automate_all():
    msg = sd_messages.cancel_automate_all
    assert (
        msg
        == "\nOkay, canceling this run. If you want to configure your project\nfor deployment, run simple_deploy again without the --automate-all flag.\n"
    )


# --- Dynamic messages ---

# DEV: This should be updated to test_invalid_plugin_msg()?
# def test_invalid_platform_msg():
#     msg = sd_messages.invalid_platform_msg("bad_platform")
#     assert (
#         msg
#         == '\n\n--- The platform "bad_platform" is not currently supported. ---\n\n- Current options are: fly_io, platform_sh, and heroku\n- Example usage:\n  $ python manage.py simple_deploy --platform fly_io\n  $ python manage.py simple_deploy --platform platform_sh\n  $ python manage.py simple_deploy --platform heroku\n\n'
#     )


def test_file_found():
    msg = sd_messages.file_found("Procfile")
    assert (
        msg == "\nThe file Procfile already exists. Is it okay to replace this file?\n"
    )


def test_file_replace_rejected():
    msg = sd_messages.file_replace_rejected("Procfile")
    assert (
        msg
        == "\nIn order to configure the project for deployment, we need to write the\nfile: Procfile\nPlease remove the current version, and then run simple_deploy again.\n"
    )
