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

cli_not_installed = """
In order to deploy to Platform.sh, you need to install the Platform.sh CLI.
  See here: https://docs.platform.sh/gettingstarted/introduction/template/cli-requirements.html
After installing the CLI, you can run simple_deploy again.
"""

platformshconfig_not_installed = """
In order to deploy to Platform.sh, you need to install the package `platformshoconfig`.
To do this, run the following command, or its equivalent in your project:
    pip install platformshconfig
After installing this package, you can run simple_deploy again.
"""

no_project_name = """
A project name could not be found.

The simple_deploy command expects that you've already run `platform create`, or
associated the local project with an existing project on Platform.sh.

If you haven't done so, run the `platform create` command and then run
simple_deploy again. You can override this warning by using
the `--deployed-project-name` flag to specify the name you want to use for the
project. This must match the name of your Platform.sh project.
"""

login_required = """
You appear to be logged out of the Platform.sh CLI. Please run the 
command `platform login`, and then run simple_deploy again.
"""

unknown_error = """
An unknown error has occurred. Do you have the Platform.sh CLI installed?
"""

success_msg = """
--- Your project is now configured for deployment on Platform.sh. ---

To deploy your project, you will need to:
- Commit the changes made in the configuration process.
- Run `platform push`
- What else?
"""
