"""A collection of messages used in flyio.py."""

# For conventions, see documentation in deploy_messages.py

from textwrap import dedent

from django.conf import settings


confirm_automate_all = """
The --automate-all flag means simple_deploy will:
- Run `fly apps create` for you, to create an empty Fly.io project.
- Run `fly postgres create`, to create a new database for your project.
- Configure your project for deployment on Fly.io.
- Commit all changes to your project that are necessary for deployment.
- Push these changes to Fly.io.
- Open your deployed project in a new browser tab.
"""

cancel_flyio = """
Okay, cancelling Fly.io configuration and deployment.
"""

# DEV: This could be moved to deploy_messages, with an arg for platform and URL.
cli_not_installed = """
In order to deploy to Fly.io, you need to install the Fly.io CLI.
  See here: https://fly.io/docs/flyctl/
After installing the CLI, you can run simple_deploy again.
"""

cli_logged_out = """
You are currently logged out of the Fly.io CLI. Please log in,
  and then run simple_deploy again.
You can log in from  the command line:
  $ fly auth login
"""

flyio_settings_found = """
There is already a Fly.io-specific settings block in settings.py. Is it okay to
overwrite this block, and everything that follows in settings.py?
"""

cant_overwrite_settings = """
In order to configure the project for deployment, we need to write a Fly.io-specific
settings block. Please remove the current Fly.io-specific settings, and then run
simple_deploy again.
"""

no_project_name = """
A suitable Fly.io app to deploy against could not be found.

The simple_deploy command expects that you've already created an app on Fly.io
to push to.

If you haven't done so, run the following command to create a new Fly.io app:

    $ fly apps create --generate-name

Then run simple_deploy again.

Note: Apps that have already been deployed to are ignored, to ensure that existing
  projects are not impacted by this deployment.
"""

create_app_failed = """
Could not create a Fly.io app.

The simple_deploy command can not proceed without a Fly.io app to deploy to.
You may have better luck with a configuration-only run, if you can create a Fly.io
app on your own. You may try the following command, and see if you can use any 
error messages to troubleshoot app creation:

    $ fly apps create --generate-name

If you can get this command to work, you can run simple_deploy again (without the
  --automate-all flag), and the rest of the process may work.
"""

cancel_no_db = """
A database is required for deployment. You may be able to create a database
  manually, and configure it to work with this app.
If you think there's a database that simple_deploy should be able to use,
  please open an issue: https://github.com/ehmatthes/django-simple-deploy/issues
"""


# --- Dynamic strings ---
# These need to be generated in functions, to display information that's determined as
# the script runs.


def region_not_found(app_name):
    """Could not find a region to deploy to."""

    msg = dedent(
        f"""
        --- A Fly.io region was not found. ---

        We need to know what region the app is going to be deployed to.
        We could not find a region in the output of:

        $ fly regions list -a {app_name}
    """
    )

    return msg


def confirm_use_org_name(org_name):
    """Confirm use of this org name to create a new project."""

    msg = dedent(
        f"""
        --- The Fly.io CLI requires an organization name when creating a new project. ---
        When using --automate-all, a project will be created on your behalf. The following
        organization name was found: {org_name}

        This organization will be used to create a new project. If this is not okay,
        enter n to cancel this operation.
    """
    )

    return msg


def confirm_create_db(db_cmd):
    """Confirm it's okay to create a Postgres database on the user's account."""

    msg = dedent(
        f"""
        A Postgres database is required to continue with deployment. If you confirm this,
        the following command will be run, to create a new database on your account:
        $ {db_cmd}
    """
    )

    return msg


def use_attached_db(db_name, users):
    """Found the db attached, with only default users and app_name-db user."""
    msg = dedent(
        f"""
        *** Found a database whose name matches the app name: {db_name} ***
        This is the naming convention used by simple_deploy, so this is
          probably a database that was created for you by a previous
          simple_deploy run.
        This database has the following users:
          {users}
        Three of these are the default users, and the fourth is the name of the 
          app (with underscores). This database appears to have been configured
          to work with this app.
    """
    )

    return msg


def use_unattached_db(db_name, users):
    """Found the db unattached, with only default users."""
    msg = dedent(
        f"""
        *** Found a database whose name matches the app name: {db_name} ***
        This is the naming convention used by simple_deploy, so this is
          probably a database that was created for you by a previous
          simple_deploy run.
        This database has the following users:
          {users}
        These are the default users for a Fly.io Postgres database. This database
          does not appear to have been used yet.
    """
    )

    return msg


def cant_use_db(db_name, users):
    """Can't use the db that was found, because it has multiple users."""
    msg = dedent(
        f"""
        Found a database whose name matches the app name: {db_name}
        This database has the following users:
          {users}
        This is more than the default set of users that a freshly-created db
          will have. It also has a user that doesn't match the name of the app.
        This situation is unexpected; if you think this situation should be handled, 
          please open an issue: https://github.com/ehmatthes/django-simple-deploy/issues
    """
    )

    return msg


def success_msg(log_output=""):
    """Success message, for configuration-only run.

    Note: This is immensely helpful; I use it just about every time I do a
      manual test run.
    """

    msg = dedent(
        f"""
        --- Your project is now configured for deployment on Fly.io ---

        To deploy your project, you will need to:
        - Commit the changes made in the configuration process.
            $ git status
            $ git add .
            $ git commit -am "Configured project for deployment."
        - Push your project to Fly.io's servers:
            $ fly deploy
        - Open your project:
            $ fly open    
        - As you develop your project further:
            - Make local changes
            - Commit your local changes
            - Run `fly deploy` again to push your changes.
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

        --- Your project should now be deployed on Fly.io ---

        It should have opened up in a new browser tab. If you see a
          "server not available" message, wait a minute or two and
          refresh the tab. It sometimes takes a few minutes for the
          server to be ready.
        - You can also visit your project at {deployed_url}

        If you make further changes and want to push them to Fly.io,
        commit your changes and then run `fly deploy`.
    """
    )
    return msg
