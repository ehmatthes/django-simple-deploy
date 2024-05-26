"""Manages all Heroku-specific aspects of the deployment process."""

import sys, os, re, json, subprocess
from itertools import takewhile

from django.conf import settings
from django.core.management.base import CommandError
from django.core.management.utils import get_random_secret_key
from django.utils.crypto import get_random_string
from django.utils.safestring import mark_safe

from simple_deploy.management.commands import deploy_messages as d_msgs
from simple_deploy.management.commands.heroku import deploy_messages as heroku_msgs

from simple_deploy.management.commands.utils import SimpleDeployCommandError
from simple_deploy.management.commands import utils as sd_utils


class PlatformDeployer:
    """Perform the initial deployment to Heroku.

    If --automate-all is used, carry out an actual deployment.
    If not, do all configuration work so the user only has to commit changes, and run
    `git push heroku main`.
    """

    def __init__(self, command):
        """Establishes connection to existing simple_deploy command object."""
        self.sd = command
        self.stdout = self.sd.stdout
        self.messages = heroku_msgs

    # --- Public methods ---

    def deploy(self, *args, **options):
        self.sd.write_output("\nConfiguring project for deployment to Heroku...")

        self._validate_platform()

        self._handle_poetry()

        if self.sd.automate_all:
            self._prep_automate_all()

        self._ensure_db()
        self._set_heroku_env_var()
        self._generate_procfile()
        self._add_gunicorn()
        self._configure_db()
        self._configure_static_files()
        self._configure_debug()
        self._configure_secret_key()
        self._modify_settings()
        self._conclude_automate_all()
        self._summarize_deployment()
        self._show_success_message()

    # --- Helper methods for deploy() ---

    def _validate_platform(self):
        """Make sure the local environment and project supports deployment to Heroku.

        Make sure CLI is installed, and user is authenticated.
        Make sure a project exists on Heroku that we can push to. (Make sure user
        already ran `heroku create`.)

        Returns:
            None

        Raises:
            SimpleDeployCommandError: If we find any reason deployment won't work.
        """
        self._check_heroku_settings()

        # Rest of validation does not apply to unit testing.
        if self.sd.unit_testing:
            self.heroku_app_name = "sample-name-11894"
            return

        self._check_cli_installed()
        self._check_cli_authenticated()
        self._check_heroku_project_available()

    def _handle_poetry(self):
        """Respond appropriately if the local project uses Poetry.

        If the project uses Poetry, generate a requirements.txt file, and override the
        initial value of self.sd.pkg_manager.

        Heroku doesn't work directly with Poetry, so we need to generate a
        requirements.txt file for the user, which we can then add requirements to. We
        should inform the user about this, as they may be used to just working with
        Poetry's requirements specification files.

        This should probably be addressed in the success message as well, and in the
        summary file. They will need to update the requirements.txt file whenever they
        install additional packages.

        Note that there may be a better way to approach this, such as adding
        requirements to Poetry files before generating the requirements.txt file for
        Heroku. It's not good to have a requirements.txt file that doesn't match what
        Poetry sees in the project.

        See Issue 31:
        https://github.com/ehmatthes/django-simple-deploy/issues/31#issuecomment-973147728

        Returns:
            None
        """
        # Making this check here keeps deploy() cleaner.
        if self.sd.pkg_manager != "poetry":
            return

        msg = "  Generating a requirements.txt file, because Heroku does not support Poetry directly..."
        self.sd.write_output(msg)

        cmd = "poetry export -f requirements.txt --output requirements.txt --without-hashes"
        output = self.sd.run_quick_command(cmd)
        self.sd.write_output(output)

        msg = "    Wrote requirements.txt file."
        self.sd.write_output(msg)

        # From this point forward, treat this user the same as anyone who's using a bare
        # requirements.txt file.
        self.sd.pkg_manager = "req_txt"
        self.sd.req_txt_path = self.sd.git_path / "requirements.txt"
        self.sd.log_info("    Package manager set to req_txt.")
        self.sd.log_info(f"    req_txt path: {self.sd.req_txt_path}")

        # Parse newly-generated requirements.txt file, and add simple_deploy if needed.
        # Optional deploy group dependencies aren't added to requirements.txt.
        self.sd._get_current_requirements()
        self.sd._add_simple_deploy_req()

    def _prep_automate_all(self):
        """Do intial work for automating entire process.
        - Create a heroku app to deploy to.
        - Create a Heroku Postgres database.

        Sets:
            str: self.heroku_app_name

        Returns:
            None
        """
        # Create heroku app.
        self.sd.write_output("  Running `heroku create`...")
        cmd = "heroku create --json"
        output_obj = self.sd.run_quick_command(cmd)
        self.sd.write_output(output_obj)

        # Get name of app.
        output_json = json.loads(output_obj.stdout.decode())
        self.heroku_app_name = output_json["name"]

        self._create_postgres_db()

    def _ensure_db(self):
        """Ensure a db is available, or create one.

        Returns:
            None
        """
        # DB not needed for unit testing.
        if self.sd.unit_testing:
            return
        # DB already created for automate-all.
        if self.sd.automate_all:
            return

        # Look for a Postgres database.
        addons_list = self.apps_list["addons"]
        db_exists = False
        for addon_dict in addons_list:
            # Look for a plan name indicating a postgres db.
            try:
                plan_name = addon_dict["plan"]["name"]
            except KeyError:
                pass
            else:
                if "heroku-postgresql" in plan_name:
                    db_exists = True
                    break

        if db_exists:
            msg = f"  Found a {plan_name} database."
            self.sd.write_output(msg)
            return

        msg = f"  Could not find an existing database. Creating one now..."
        self.sd.write_output(msg)
        self._create_postgres_db()

    def _set_heroku_env_var(self):
        """Set a config var to indicate when we're in the Heroku environment.
        This is mostly used to modify settings for the deployed project.
        """
        if self.sd.unit_testing:
            return

        self.sd.write_output("  Setting Heroku environment variable...")
        cmd = "heroku config:set ON_HEROKU=1"
        output = self.sd.run_quick_command(cmd)
        self.sd.write_output(output)
        self.sd.write_output("    Set ON_HEROKU=1.")
        self.sd.write_output("    This is used to define Heroku-specific settings.")

    def _check_heroku_settings(self):
        """Check to see if a Heroku settings block already exists.

        If so, ask if we can overwrite that block. This is much simpler than trying to
        keep track of individual settings.

        Returns:
            None

        Raises:
            SimpleDeployCommandError: If we can't overwrite existing Heroku-specific
            settings block.
        """
        settings_lines = self.sd.settings_path.read_text().splitlines()

        heroku_settings_start = "# Heroku settings."
        if not heroku_settings_start in settings_lines:
            self.sd.log_info("No Heroku-specific settings block found.")
            return

        # A Heroku-specific settings block exists. Get permission to overwrite it.
        if not self.sd.get_confirmation(self.messages.heroku_settings_found):
            raise SimpleDeployCommandError(self.sd, self.messages.cant_overwrite_settings)

        # Heroku-specific settings exist, but we can remove them and start fresh.
        settings_lines = list(takewhile(
            lambda line: line!=heroku_settings_start, settings_lines))
        settings_text = "\n".join(settings_lines)
        self.sd.settings_path.write_text(settings_text)

        self.sd.write_output("  Removed existing Heroku-specific settings block.")

    def _generate_procfile(self):
        """Create Procfile, if none present."""

        #   Procfile should be in project root, if present.
        self.sd.write_output(f"\n  Looking in {self.sd.git_path} for Procfile...")
        procfile_present = "Procfile" in os.listdir(self.sd.git_path)

        if procfile_present:
            self.sd.write_output("    Found existing Procfile.")
        else:
            self.sd.write_output("    No Procfile found. Generating Procfile...")
            if self.sd.nested_project:
                proc_command = f"web: gunicorn {self.sd.local_project_name}.{self.sd.local_project_name}.wsgi --log-file -"
            else:
                proc_command = (
                    f"web: gunicorn {self.sd.local_project_name}.wsgi --log-file -"
                )

            with open(f"{self.sd.git_path}/Procfile", "w") as f:
                f.write(proc_command)

            self.sd.write_output("    Generated Procfile with following process:")
            self.sd.write_output(f"      {proc_command}")

    def _add_gunicorn(self):
        """Add gunicorn to project requirements."""
        self.sd.add_package("gunicorn")

    def _configure_db(self):
        """Add required db-related packages, and modify settings for Heroku db."""
        self.sd.write_output("\n  Configuring project for Heroku database...")
        self._add_db_packages()
        # self._add_db_settings()

    def _add_db_packages(self):
        """Add packages required for the Heroku db."""
        self.sd.write_output("    Adding db-related packages...")

        # psycopg2 2.9 causes "database connection isn't set to UTC" issue.
        #   See: https://github.com/ehmatthes/heroku-buildpack-python/issues/31
        self.sd.add_package("psycopg2")
        self.sd.add_package("dj-database-url")

    def _configure_static_files(self):
        """Configure static files for Heroku deployment."""

        self.sd.write_output("\n  Configuring static files for Heroku deployment...")

        # Add whitenoise to requirements.
        self.sd.write_output("    Adding staticfiles-related packages...")
        self.sd.add_package("whitenoise")

        # Modify settings, and add a directory for static files.
        # self._add_static_file_settings()
        self._add_static_file_directory()

    def _add_static_file_directory(self):
        """Create a folder for static files, if it doesn't already exist."""
        self.sd.write_output("    Checking for static files directory...")

        # Make sure there's a static files directory.
        static_files_dir = f"{self.sd.project_root}/static"
        if os.path.exists(static_files_dir):
            if os.listdir(static_files_dir):
                self.sd.write_output("    Found non-empty static files directory.")
                return
        else:
            os.makedirs(static_files_dir)
            self.sd.write_output("    Created empty static files directory.")

        # Add a placeholder file to the empty static files directory.
        placeholder_file = f"{static_files_dir}/placeholder.txt"
        with open(placeholder_file, "w") as f:
            f.write(
                "This is a placeholder file to make sure this folder is pushed to Heroku."
            )
        self.sd.write_output("    Added placeholder file to static files directory.")

    def _configure_debug(self):
        """Use an env var to manage DEBUG setting, and set to False."""

        # Config variables are strings, which always causes confusion for people
        #   when setting boolean env vars. A good habit is to use something other than
        #   True or False, so it's clear we're not trying to use Python's default
        #   boolean values.
        # Here we use 'TRUE' and 'FALSE'. Then a simple test:
        #    os.environ.get('DEBUG') == 'TRUE'
        # returns the bool value True for 'TRUE', and False for 'FALSE'.
        # Taken from: https://stackoverflow.com/a/56828137/748891

        if self.sd.unit_testing:
            return

        self.sd.write_output("  Setting DEBUG env var...")
        cmd = "heroku config:set DEBUG=FALSE"
        output = self.sd.run_quick_command(cmd)
        self.sd.write_output(output)
        self.sd.write_output("    Set DEBUG config variable to FALSE.")

    def _configure_secret_key(self):
        """Use an env var to manage the secret key."""
        if self.sd.unit_testing:
            return

        # Generate a new key.
        if self.sd.on_windows:
            # Non-alphanumeric keys have been problematic on Windows.
            new_secret_key = get_random_string(
                length=50, allowed_chars="abcdefghijklmnopqrstuvwxyz0123456789"
            )
        else:
            new_secret_key = get_random_secret_key()

        # Set the new key as an env var on Heroku.
        self.sd.write_output("  Setting new secret key for Heroku...")
        cmd = f"heroku config:set SECRET_KEY={new_secret_key}"
        output = self.sd.run_quick_command(cmd, skip_logging=True)
        self.sd.write_output(output)
        self.sd.write_output("    Set SECRET_KEY config variable.")

    def _modify_settings(self):
        """Add Heroku-specific settings.

        This settings block is currently the same for all users. The ALLOWED_HOSTS
        setting should be customized.
        """
        self.sd.write_output("\n  Adding a Heroku-specific settings block...")

        settings_string = self.sd.settings_path.read_text()
        safe_settings_string = mark_safe(settings_string)
        context = {"current_settings": safe_settings_string}
        sd_utils.write_file_from_template(self.sd.settings_path, "settings.py", context)

        msg = f"    Modified settings.py file: {self.sd.settings_path}"
        self.sd.write_output(msg)

    def _conclude_automate_all(self):
        """Finish automating the push to Heroku."""
        # Making this check here lets deploy() be cleaner.
        if not self.sd.automate_all:
            return

        self.sd.commit_changes()

        self.sd.write_output("  Pushing to heroku...")

        # Get the current branch name. Get the first line of status output,
        #   and keep everything after "On branch ".
        cmd = "git status"
        git_status = self.sd.run_quick_command(cmd)
        self.sd.write_output(git_status)
        status_str = git_status.stdout.decode()
        self.current_branch = status_str.split("\n")[0][10:]

        # Push current local branch to Heroku main branch.
        # This process usually takes a minute or two, which is longer than we
        #   want users to wait for console output. So rather than capturing
        #   output with subprocess.run(), we use Popen and stream while logging.
        # DEV: Note that the output of `git push heroku` goes to stderr, not stdout.
        self.sd.write_output(f"    Pushing branch {self.current_branch}...")
        if self.current_branch in ("main", "master"):
            cmd = f"git push heroku {self.current_branch}"
        else:
            cmd = f"git push heroku {self.current_branch}:main"
        self.sd.run_slow_command(cmd)

        # Run initial set of migrations.
        self.sd.write_output("  Migrating deployed app...")
        if self.sd.nested_project:
            cmd = f"heroku run python {self.sd.local_project_name}/manage.py migrate"
        else:
            cmd = "heroku run python manage.py migrate"
        output = self.sd.run_quick_command(cmd)

        self.sd.write_output(output)

        # Open Heroku app, so it simply appears in user's browser.
        self.sd.write_output("  Opening deployed app in a new browser tab...")
        cmd = "heroku open"
        output = self.sd.run_quick_command(cmd)
        self.sd.write_output(output)

    def _summarize_deployment(self):
        """Manage all tasks related to generating and showing the friendly
        summary of the deployment.

        This does not take the place of the platform's official documentation.
          Instead, it gives the user a friendly entry into the platform's
          official documentation. It also gives them a brief summary of some
          followup steps they can take, for example making a second push, or
          changing the URL of the deployed app.
        """
        self._generate_summary()

    def _show_success_message(self):
        """After a successful run, show a message about what to do next."""

        # DEV:
        # - Say something about DEBUG setting.
        #   - Should also consider setting DEBUG = False in the Heroku-specific
        #     settings.
        # - Mention that this script should not need to be run again, unless
        #   creating a new deployment.
        #   - Describe ongoing approach of commit, push, migrate. Lots to consider
        #     when doing this on production app with users, make sure you learn.

        if self.sd.automate_all:
            # Show how to make future deployments.
            msg = self.messages.success_msg_automate_all(
                self.heroku_app_name, self.current_branch
            )
        else:
            # Show steps to finish the deployment process.
            msg = self.messages.success_msg(self.sd.pkg_manager, self.heroku_app_name)

        self.sd.write_output(msg)

    # --- Utility methods ---

    def _check_cli_installed(self):
        """Verify the Heroku CLI is installed on the user's system.

        Returns:
            None

        Raises:
            SimpleDeployCommandError: If CLI not installed.
        """
        cmd = "heroku --version"
        try:
            output_obj = self.sd.run_quick_command(cmd)
        except FileNotFoundError:
            # This generates a FileNotFoundError on Linux (Ubuntu) if CLI not installed.
            raise SimpleDeployCommandError(self.sd, self.messages.cli_not_installed)

        self.sd.log_info(output_obj)

        # The returncode for a successful command is 0, so anything truthy means the
        # command errored out.
        if output_obj.returncode:
            raise SimpleDeployCommandError(self.sd, self.messages.cli_not_installed)

    def _check_cli_authenticated(self):
        """Verify the user has authenticated with the CLI.

        Returns:
            None

        Raises:
            SimpleDeployCommandError: If the user has not been authenticated.
        """
        cmd = "heroku auth:whoami"
        output_obj = self.sd.run_quick_command(cmd)
        self.sd.log_info(output_obj)

        output_str = output_obj.stderr.decode()
        if "Error: Invalid credentials provided" in output_str:
            raise SimpleDeployCommandError(self.sd, self.messages.cli_not_authenticated)

    def _check_heroku_project_available(self):
        """Verify that a Heroku project is available to push to.

        Returns:
            None

        Raises:
            SimpleDeployCommandError: If there's no app to push to.

        Sets:
            dict: self.apps_list
            str: self.heroku_app_name
        """
        # automate-all does the work we're checking for here.
        if self.sd.automate_all:
            return

        self.sd.write_output("  Looking for Heroku app to push to...")
        cmd = "heroku apps:info --json"
        output_obj = self.sd.run_quick_command(cmd)
        self.sd.write_output(output_obj)

        output_str = output_obj.stdout.decode()

        # If output_str is emtpy, there is no heroku app.
        if not output_str:
            raise SimpleDeployCommandError(
                self.sd, self.messages.no_heroku_app_detected
            )

        # Parse output for app_name.
        self.apps_list = json.loads(output_str)
        app_dict = self.apps_list["app"]
        self.heroku_app_name = app_dict["name"]
        self.sd.write_output(f"    Found Heroku app: {self.heroku_app_name}")

    def _create_postgres_db(self):
        """Create a Heroku Postgres database.

        Returns:
            None
        """
        self.sd.write_output("  Creating Postgres database...")
        cmd = "heroku addons:create heroku-postgresql:essential-0"
        output = self.sd.run_quick_command(cmd)
        self.sd.write_output(output)

    def _generate_summary(self):
        """Generate the friendly summary, which is html for now."""
        # Generate the summary file.
        path = self.sd.log_dir_path / "deployment_summary.html"

        summary_str = "<h2>Understanding your deployment</h2>"
        path.write_text(summary_str, encoding="utf-8")

        msg = f"\n  Generated friendly summary: {path}"
        self.sd.write_output(msg)
