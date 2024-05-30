"""A collection of messages used in deploy_platformsh.py."""

# For conventions, see documentation in deploy_messages.py

from textwrap import dedent

from django.conf import settings


confirm_automate_all = """
The --automate-all flag means simple_deploy will:
- Run `platform create` for you, to create an empty Platform.sh project.
  - This will create a project in the us-3.platform.sh region. If you wish
    to use a different region, cancel this operation and use the --region flag.
  - You can see a list of all regions by running `platform help project:create`
- Commit all changes to your project that are necessary for deployment.
- Push these changes to Platform.sh.
- Open your deployed project in a new browser tab.
"""

cancel_plsh = """
Okay, cancelling platform.sh deployment.
"""

cli_not_installed = """
In order to deploy to Platform.sh, you need to install the Platform.sh CLI.
  See here: https://docs.platform.sh/gettingstarted/introduction/template/cli-requirements.html
After installing the CLI, you can run simple_deploy again.
"""

cli_logged_out = """
You are currently logged out of the Platform.sh CLI. Please log in,
  and then run simple_deploy again.
You can log in from  the command line:
  $ platform login
"""

plsh_settings_found = """
There is already a Platform.sh-specific settings block in settings.py. Is it okay to
overwrite this block, and everything that follows in settings.py?
"""

cant_overwrite_settings = """
In order to configure the project for deployment, we need to write a Platform.sh-specific
settings block. Please remove the current Platform.sh-specific settings, and then run
simple_deploy again.
"""

no_project_name = """
A Platform.sh project name could not be found.

The simple_deploy command expects that you've already run `platform create`, or
associated the local project with an existing project on Platform.sh.

If you haven't done so, run the `platform create` command and then run
simple_deploy again. You can override this warning by using
the `--deployed-project-name` flag to specify the name you want to use for the
project. This must match the name of your Platform.sh project.
"""

org_not_found = """
A Platform.sh organization name could not be found.

You may have created a Platform.sh account, but not created an organization.
The Platform.sh CLI requires an organization name when creating a new project.

Please visit the Platform.sh console and make sure you have created an organization.
You can also do this through the CLI using the `platform organization:create` command.
For help, run `platform help organization:create`.
"""

no_org_available = """
A Platform.sh org must be used to make a deployment. Please identify or create the org
you'd like to use, and then try again.
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


def confirm_use_org(org_name):
    """Confirm use of this org to create a new project."""

    msg = dedent(
        f"""
        --- The Platform.sh CLI requires an organization name when creating a new project. ---
        When using --automate-all, a project will be created on your behalf. The following
        organization was found: {org_name}

        This organization will be used to create a new project. If this is not okay,
        enter n to cancel this operation.
    """
    )

    return msg


def unknown_create_error(e):
    """Process a non-specific error when running `platform create`
    while using automate_all. This is most likely an issue with the user
    not having permission to create a new project, for example because they
    are on a trial plan and have already created too many projects.
    """

    msg = dedent(
        f"""
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
    """
    )

    return msg


def success_msg(log_output=""):
    """Success message, for configuration-only run."""

    msg = dedent(
        f"""
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
            - Commit your local changes
            - Run `platform push`
    """
    )

    if log_output:
        msg += dedent(
            f"""
        - You can find a full record of this configuration in the simple_deploy_logs directory.
        """
        )

    return msg


def success_msg_automate_all(deployed_url):
    """Success message, when using --automate-all."""

    msg = dedent(
        f"""

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

    """
    )
    return msg
