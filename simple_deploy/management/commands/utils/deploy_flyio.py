"""Manages all Fly.io-specific aspects of the deployment process."""

# Note: Internal references to Fly.io will almost always be flyio.
#   Public references, such as the --platform argument, will be fly_io.

import sys, os, re, subprocess
from pathlib import Path

from django.conf import settings
from django.core.management.base import CommandError
from django.core.management.utils import get_random_secret_key
from django.utils.crypto import get_random_string
from django.template.engine import Engine
from django.template.loaders.app_directories import Loader
from django.template.loader import render_to_string
from django.utils.safestring import mark_safe

from simple_deploy.management.commands.utils import deploy_messages as d_msgs
from simple_deploy.management.commands.utils import deploy_messages_flyio as flyio_msgs


class FlyioDeployer:
    """Perform the initial deployment of a simple project.
    Configure as much as possible automatically.
    """

    def __init__(self, command):
        """Establishes connection to existing simple_deploy command object."""
        self.sd = command
        self.stdout = self.sd.stdout


    def deploy(self, *args, **options):
        self.sd.write_output("Configuring project for deployment to Fly.io...")

        # self._add_platformsh_settings()

        # # DEV: Group this with later yaml generation methods.
        # self._generate_platform_app_yaml()

        # # DEV: These can be done in one pass.
        # self._add_platformshconfig()
        # self._add_gunicorn()
        # self._add_psycopg2()

        # # DEV: These could be refactored.
        # self._make_platform_dir()
        # self._generate_routes_yaml()
        # self._generate_services_yaml()

        # self._conclude_automate_all()

        # self._show_success_message()


    # --- Methods called from simple_deploy.py ---

    def confirm_preliminary(self):
        """Deployment to Fly.io is in a preliminary state, and we need to be
        explicit about that.
        """
        # Skip this confirmation when unit testing.
        if self.sd.unit_testing:
            return

        self.stdout.write(flyio_msgs.confirm_preliminary)
        confirmed = self.sd.get_confirmation(skip_logging=True)

        if confirmed:
            self.stdout.write("  Continuing with Fly.io deployment...")
        else:
            # Quit and invite the user to try another platform.
            # We are happily exiting the script; there's no need to raise a
            #   CommandError.
            self.stdout.write(flyio_msgs.cancel_flyio)
            sys.exit()


    def validate_platform(self):
        """Make sure the local environment and project supports deployment to
        Fly.io.
        
        The returncode for a successful command is 0, so anything truthy means
          a command errored out.
        """
        self._validate_cli()

        # When running unit tests, will not be logged into CLI.
        if not self.sd.unit_testing:
            self.deployed_project_name = self._get_deployed_project_name()
            self.region = self._get_region()
            # Create the db now, before any additional configuration.
            self._create_db()
        else:
            self.deployed_project_name = self.sd.deployed_project_name


        print('DEV exit')
        sys.exit()


    # --- Helper methods for methods called from simple_deploy.py ---

    def _validate_cli(self):
        """Make sure the Platform.sh CLI is installed."""
        cmd = 'flyctl version'
        output_obj = self.sd.execute_subp_run(cmd)
        if output_obj.returncode:
            raise CommandError(flyio_msgs.cli_not_installed)

    def _get_deployed_project_name(self):
        """Get the Fly.io project name.
        Parse the output of `flyctl apps list`, and look for an app name
          that doesn't have a value set for LATEST DEPLOY. This indicates
          an app that has just been created, and has not yet been deployed.

        Returns:
        - String representing deployed project name.
        - Raises CommandError if deployed project name can't be found.
        """
        msg = "\nLooking for Fly.io app to deploy against..."
        self.sd.write_output(msg, skip_logging=True)

        # Get apps info.
        cmd = "flyctl apps list"
        output_obj = self.sd.execute_subp_run(cmd)
        output_str = output_obj.stdout.decode()

        # Only keep relevant output; get rid of blank lines, update messages,
        #   and line with labels like NAME and LATEST DEPLOY.
        lines = output_str.split('\n')
        lines = [line for line in lines if line]
        lines = [line for line in lines if 'update' not in line.lower()]
        lines = [line for line in lines if 'NAME' not in line]
        lines = [line for line in lines if 'builder' not in line]

        # An app that has not been deployed to will only have values set for NAME,
        #   OWNER, and STATUS. PLATFORM and LATEST DEPLOY will be empty.
        app_name = ''
        for line in lines:
            # The desired line has three elements.
            parts = line.split()
            if len(parts) == 3:
                app_name = parts[0]

        # Return deployed app name, or raise CommandError.
        if app_name:
            msg = f"  Found Fly.io app: {app_name}"
            self.sd.write_output(msg, skip_logging=True)
            return app_name
        else:
            # Can't continue without a Fly.io app to configure against.
            raise CommandError(flyio_msgs.no_project_name)

    def _get_region(self):
        """Get the region that the Fly.io app is configured for. We'll need this
        to create a postgres database.

        Parse the output of `flyctl regions list -a app_name`.

        Returns:
        - String representing region.
        - Raises CommandError if can't find region.
        """

        msg = "Looking for Fly.io region..."
        self.sd.write_output(msg, skip_logging=True)

        # Get region output.
        cmd = f"flyctl regions list -a {self.deployed_project_name}"
        output_obj = self.sd.execute_subp_run(cmd)
        output_str = output_obj.stdout.decode()

        # Look for first three-letter line after Region Pool.
        region = ''
        pool_found = False
        lines = output_str.split('\n')
        for line in lines:
            if not pool_found and "Region Pool" in line:
                pool_found = True
                continue

            # This is the first line after Region Pool.
            if pool_found:
                region = line.strip()
                break

        # Return region name, or raise CommandError.
        if region:
            msg = f"  Found region: {region}"
            self.sd.write_output(msg, skip_logging=True)
            return region
        else:
            # Can't continue without a Fly.io region to configure against.
            raise CommandError(flyio_msgs.region_not_found(self.deployed_project_name))

    def _create_db(self):
        """Create a db to deploy to, if none exists.
        Returns: 
        - 
        - Raises CommandError if...
        """
        msg = "Looking for a Postgres database..."
        self.sd.write_output(msg, skip_logging=True)

        db_exists = self._check_if_db_exists()

        if db_exists:
            return

        # No db found, create a new db.
        msg = f"  Create a new Postgres database..."
        cmd = f"flyctl postgres create --name {self.deployed_project_name}-db --region {self.region}"
        cmd += " --initial-cluster-size 1 --vm-size shared-cpu-1x --volume-size 1"
        print("cmd:", cmd)

    def _check_if_db_exists(self):
        """Check if a postgres db already exists that should be used with this app.
        Returns:
        - True if db found.
        - False if not found.
        """

        # First, see if any Postgres clusters exist.
        cmd = "flyctl postgres list"
        output_obj = self.sd.execute_subp_run(cmd)
        output_str = output_obj.stdout.decode()

        if "No postgres clusters found" in output_str:
            msg = "  No Postgres database found."
            self.sd.write_output(msg, skip_logging=True)
            return False
        else:
            msg = "  A Postgres database was found."
            self.sd.write_output(msg, skip_logging=True)
            return True