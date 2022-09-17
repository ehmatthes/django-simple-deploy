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

cancel_no_db = """
A database is required for deployment. You may be able to create a database
manually, and configure it to work with this app.
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


def confirm_create_db(db_cmd):
    """Confirm it's okay to create a Postgres database on the user's account."""

    msg = dedent(f"""
        A Postgres database is required to continue with deployment. If you confirm this,
        the following command will be run, to create a new database on your account:
        $ {db_cmd}
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


