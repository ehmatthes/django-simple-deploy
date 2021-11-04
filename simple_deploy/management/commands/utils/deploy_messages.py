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
# - Any message used when raising a CommandError should have the first line
#   immediately after the opening triple quote, so it appears right after
#   "CommandError: ".
# - This should be followed by a blank line, to emphasize the detailed
#   information in the error message.
#
# Line length conventions
# - DynamicMessages
#  - It can be helpful to make a second vertical line at 90 characters
#    (78 characters + three indentation levels) to judge the line lengths
#    for dynamic messages.


from textwrap import dedent

from django.conf import settings


confirm_automate_all = """
The --automate-all flag means simple_deploy will:
- Run `heroku create` for you, to create a new Heroku project.
- Commit all changes to your project that are necessary for deployment.
  - These changes will be committed to the current branch, so you may want
    to make a new branch for this work.
- Push these changes to Heroku.
- Run the initial set of migrations to set up the remote database.
- Open your deployed project in a new browser tab.
"""

cancel_automate_all = """
Okay, canceling this run. If you want to configure your project
for deployment, run simple_deploy again without the --automate-all flag.
"""

no_heroku_app_detected = """No Heroku app name has been detected.

- The simple_deploy command assumes you have already run 'heroku create'
  to start the deployment process.
- Please run 'heroku create', and then run
  'python manage.py simple_deploy' again.
- If you haven't already done so, you will need to install the Heroku CLI:
  https://devcenter.heroku.com/articles/heroku-cli
"""


# --- Dynamic strings ---

class DynamicMessages:
    """Messages that require information generated in simple_deploy.py."""

    def __init__(self, sd_command):
        """Gets a copy of the simple_deploy Command object, which has
        references to all information needed to generate any dynamic message.
        """
        # Don't do everything in __init__(); may want to break this up into
        #   defining groups of messages.
        # self.sd_command = sd_command
        pass


    def get_allowed_hosts_not_empty_msg(self, heroku_host):
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



