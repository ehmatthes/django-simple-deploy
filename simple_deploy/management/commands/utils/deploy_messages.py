"""A collection of messages used in simple_deploy.py."""

# Module is called deploy_messages to avoid collisions with any messages.py 
#   files.
#
# Storing messages here makes for a much shorter simple_deploy.py file, and
#   makes it easier to see how the messages actually look on screen. The 
#   disadvantage is that it's harder to track what messages are being
#   displayed when working on simple_deploy.
# When you add a message here, make sure the stdout.write() call has a comment
#   that clearly summarizes what the message says.
#
# CommandError messages
# - Any message used when raising a CommandError should have a blank line after
#   the line with the opening triple quote, to separate the main error message
#   from the generic "Command Error".
#
# Line length conventions
# - Try to keep lines at the 79-char PEP 8 limit, but the project is not
#   overly strict about it at this point.
#
# - DynamicMessages
#   - It can be helpful to make a second vertical line at 86 characters
#     (78 characters + two indentation levels) to judge the line lengths
#     for dynamic messages.


from textwrap import dedent

from django.conf import settings


cancel_automate_all = """
Okay, canceling this run. If you want to configure your project
for deployment, run simple_deploy again without the --automate-all flag.
"""


# --- Dynamic strings ---
# These need to be generated in functions, to display information that's 
#   determined as the script runs.

def allowed_hosts_not_empty_msg(host):
    # This will be displayed as a CommandError.
    # DEV: This should no longer be called from deploy_heroku.py, so it's only
    #   here until the approach to ALLOWED_HOSTS in deploy_azure.py is simplified.
    msg = dedent(f"""

        Your ALLOWED_HOSTS setting is not empty, and it does not contain {host}.
        - ALLOWED_HOSTS is a critical security setting.
        - It is empty by default, which means you or someone else has decided where this project can be hosted.
        - Your ALLOWED_HOSTS setting currently contains the following entries:
          {settings.ALLOWED_HOSTS}"
        - We don't know enough about your project to add to or override this setting.
        - If you want to continue with this deployment, make sure ALLOWED_HOSTS
          is either empty, or contains the host {host}.
        - Once you have addressed this issue, you can run the simple_deploy command
          again, and it will pick up where it left off.
    """)
    return msg


def allowed_hosts_not_empty_msg(heroku_host):
    # This will be displayed as a CommandError.
    msg = dedent(f"""

        Your ALLOWED_HOSTS setting is not empty, and it does not contain {heroku_host}.
        - ALLOWED_HOSTS is a critical security setting.
        - It is empty by default, which means you or someone else has decided where this project can be hosted.
        - Your ALLOWED_HOSTS setting currently contains the following entries:
          {settings.ALLOWED_HOSTS}"
        - We don't know enough about your project to add to or override this setting.
        - If you want to continue with this deployment, make sure ALLOWED_HOSTS
          is either empty, or contains the host {heroku_host}.
        - Once you have addressed this issue, you can run the simple_deploy command
          again, and it will pick up where it left off.
    """)
    return msg