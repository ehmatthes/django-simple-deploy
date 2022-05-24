"""A collection of messages used in deploy_heroku.py."""

# For conventions, see documentation in deploy_messages.py

from textwrap import dedent

from django.conf import settings


confirm_preliminary = """
***** Deployments to platform.sh are experimental at this point ***

- Support for deploying to platform.sh is in an exploratory phase at this point.
- You should only be using this project to deploy to platform.sh at this point if
  you are interested in helping to develop or test the simple_deploy project.
- You should look at the deploy_platformsh.py script before running this command,
  so you know what kinds of changes will be made to your project.
- You should understand the platform.sh console, and be comfortable deleting resources
  that are created during this deployment.
- You may want to cancel this run and deploy to Heroku instead. You can do this
  explicitly with the `--platform heroku` argument, or you can leave out the
  `--platform` argument and simple_deploy will deploy to Heroku by default.
"""

cancel_plsh = """
Okay, cancelling platform.sh deployment.
"""

success_msg = """
--- Your project is now configured for deployment on platform.sh. ---

To deploy your project, you will need to:
- Commit the changes made in the configuration process.
- Run `platform push`
- What else?
"""
