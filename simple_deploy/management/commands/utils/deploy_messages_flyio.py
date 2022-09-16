"""A collection of messages used in flyio.py."""

# For conventions, see documentation in deploy_messages.py

from textwrap import dedent

from django.conf import settings


confirm_preliminary = """
***** Deployments to Fly.io are experimental at this point ***

- Support for deploying to Fly.io is in an exploratory phase at this point.
- You should only be using this project to deploy to Fly.io at this point if
  you are interested in helping to develop or test the simple_deploy project.
- You should look at the deploy_flyio.py script before running this command,
  so you know what kinds of changes will be made to your project.
- You should understand the Fly.io console, and be comfortable deleting resources
  that are created during this deployment.
- You may want to cancel this run and deploy to a different platform.
"""

cancel_flyio = """
Okay, cancelling Fly.io deployment.
"""

# DEV: Update URL
# DEV: This could be moved to deploy_messages, with an arg for platform and URL.
cli_not_installed = """
In order to deploy to Fly.io, you need to install the Fly.io CLI.
  See here: fly_io_url
After installing the CLI, you can run simple_deploy again.
"""

no_project_name = """
A Fly.io app name could not be found.

The simple_deploy command expects that you've already created an app on Fly.io
to push to.

If you haven't done so, run the following command to create a new Fly.io app:

$ flyctl apps create --generate-name

Then run simple_deploy again.
"""










org_not_found = """
A Platform.sh organization name could not be found.

You may have created a Platform.sh account, but not created an organization.
The Platform.sh CLI requires an organization name when creating a new project.

Please visit the Platform.sh console and make sure you have created an organization.
You can also do this through the CLI using the `platform organization:create` command.
For help, run `platform help organization:create`.
"""

login_required = """
You appear to be logged out of the Platform.sh CLI. Please run the 
command `platform login`, and then run simple_deploy again.

You may be able to override this error by passing the `--deployed-project-name`
flag.
"""

unknown_error = """
An unknown error has occurred. Do you have the Platform.sh CLI installed?
"""

may_configure = """
You may want to re-run simple_deploy without the --automate-all flag.

You will have to create the Platform.sh project yourself, but simple_deploy
will do all of the necessary configuration for deployment.
"""


# --- Dynamic strings ---
# These need to be generated in functions, to display information that's 
#   determined as the script runs.

def region_not_found(app_name):
    """Could not find a region to deploy to."""

    msg = dedent(f"""
        --- A Fly.io region was not found. ---

        We need to know what region the app is going to be deployed to.
        We could not find a region in the output of:

        $ flyctl regions list -a {app_name}
    """)

    return msg
    

def confirm_use_org_name(org_name):
    """Confirm use of this org name to create a new project."""

    msg = dedent(f"""
        --- The Platform.sh CLI requires an organization name when creating a new project. ---
        When using --automate-all, a project will be created on your behalf. The following
        organization name was found: {org_name}

        This organization will be used to create a new project. If this is not okay,
        enter n to cancel this operation.
    """)

    return msg


def unknown_create_error(e):
    """Process a non-specific error when running `platform create` 
    while using automate_all. This is most likely an issue with the user
    not having permission to create a new project, for example because they
    are on a trial plan and have already created too many projects.
    """

    msg = dedent(f"""
        --- An error has occurred when trying to create a new Platform.sh project. ---

        While running `platform create`, an error has occurred. You should check
        the Platform.sh console to see if a project was partially created.

        The error messages that Platform.sh provides, both through the CLI and
        the console, are not always specific enough to be helpful. For example, 
        newer users are limited to two new projects in a 24-hour period, or something
        like that. But if you try to create an additional project, you only get
        a message that says: "You do not have access to create a new Subscriptions resource".
        There is no information about specific limits, and how to address them.

        The following output may help diagnose the error:
        ***** output of `platform create` *****

        {e.stderr.decode()}

        ***** end output *****
    """)

    return msg


def success_msg(log_output=''):
    """Success message, for configuration-only run."""

    msg = dedent(f"""
        --- Your project is now configured for deployment on Platform.sh. ---

        To deploy your project, you will need to:
        - Commit the changes made in the configuration process.
            $ git status
            $ git add .
            $ git commit -am "Configured project for deployment."
        - Push your project to Platform.sh' servers:
            $ platform push
        - Open your project:
            $ platform url    
        - As you develop your project further:
            - Make local changes
            - Commmit your local changes
            - Run `platform push`
    """)

    if log_output:
        msg += dedent(f"""
        - You can find a full record of this configuration in the simple_deploy_logs directory.
        """)

    return msg


def success_msg_automate_all(deployed_url):
    """Success message, when using --automate-all."""

    msg = dedent(f"""

        --- Your project should now be deployed on Platform.sh. ---

        It should have opened up in a new browser tab.
        - You can also visit your project at {deployed_url}

        If you make further changes and want to push them to Platform.sh,
        commit your changes and then run `platform push`.

        Also, if you haven't already done so you should review the
        documentation for Python deployments on Platform.sh at:
        - https://docs.platform.sh/languages/python.html
        - This documentation will help you understand how to maintain
          your deployment.

    """)
    return msg