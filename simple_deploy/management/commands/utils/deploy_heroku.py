"""Manages all Heroku-specific aspects of the deployment process."""

import sys, os, re, subprocess

from django.conf import settings
from django.core.management.base import CommandError
from django.core.management.utils import get_random_secret_key
from django.utils.crypto import get_random_string

from simple_deploy.management.commands.utils import deploy_messages as d_msgs
from simple_deploy.management.commands.utils import deploy_messages_heroku as dh_msgs


class HerokuDeployer:
    """Perform the initial deployment of a simple project.
    Configure as much as possible automatically.
    """

    def __init__(self, command):
        """Establishes connection to existing simple_deploy command object."""
        self.sd = command
        self.stdout = self.sd.stdout


    def deploy(self, *args, **options):
        self.sd.write_output("Configuring project for deployment to Heroku...")

        self._prep_automate_all()
        self._get_heroku_app_info()
        self._set_heroku_env_var()
        self._get_heroku_settings()
        self.sd._add_simple_deploy_req()
        self._generate_procfile()
        self._add_gunicorn()
        self._check_allowed_hosts()
        self._configure_db()
        self._configure_static_files()
        self._configure_debug()
        self._configure_secret_key()
        self._conclude_automate_all()
        self._summarize_deployment()
        self._show_success_message()


    def _prep_automate_all(self):
        """Do intial work for automating entire process."""
        # This is platform-specific, because we want to specify exactly what
        #   will be automated.

        # Skip this prep work if --automate-all not used.
        if not self.sd.automate_all:
            return

        # Confirm the user knows exactly what will be automated.
        self.sd.write_output(dh_msgs.confirm_automate_all)

        # Get confirmation.
        confirmed = ''
        while confirmed.lower() not in ('y', 'yes', 'n', 'no'):
            prompt = "\nAre you sure you want to do this? (yes|no) "
            self.sd.write_output(prompt)
            confirmed = input()
            self.sd.write_output(confirmed, write_to_console=False)

            if confirmed.lower() not in ('y', 'yes', 'n', 'no'):
                self.sd.write_output("  Please answer yes or no.")

        if confirmed.lower() in ('y', 'yes'):
            self.sd.write_output("  Running `heroku create`...")
            cmd = 'heroku create'
            output = self.sd.execute_subp_run(cmd)
            self.sd.write_output(output)
        else:
            # Quit and have the user run the command again; don't assume not
            #   wanting to automate means they want to configure.
            self.sd.write_output(d_msgs.cancel_automate_all)
            sys.exit()


    def _get_heroku_app_info(self):
        """Get info about the Heroku app we're pushing to."""
        # We assume the user has already run 'heroku create', or --automate-all
        #   has run it. If it hasn't been run, we'll quit and tell them to do so.

        # DEV: The testing approach here should be improved. We should be able
        #   to easily test for a failed apps:info call. Also, probably want
        #   to mock the output of apps:info rather than directly setting
        #   heroku_app_name.
        if self.sd.local_test:
            self.heroku_app_name = 'sample-name-11894'
        else:
            self.sd.write_output("  Inspecting Heroku app...")
            cmd = 'heroku apps:info'
            apps_info = self.sd.execute_subp_run(cmd)
            self.sd.write_output(apps_info)

            # Turn stdout info into a list of strings that we can then parse.
            #   If no app exists, stdout is empty and the output went to stderr.
            apps_info = apps_info.stdout.decode().split('\n')
            # DEV: Use this code when we can require Python >=3.9.
            # self.heroku_app_name = apps_info[0].removeprefix('=== ')
            self.heroku_app_name = apps_info[0].replace('=== ', '')

        if self.heroku_app_name:
            self.sd.write_output(f"    Found Heroku app: {self.heroku_app_name}")
        else:
            # Let user know they need to run `heroku create`.
            self.sd.write_output(dh_msgs.no_heroku_app_detected,
                write_to_console=False)
            raise CommandError(dh_msgs.no_heroku_app_detected)


    def _set_heroku_env_var(self):
        """Set a config var to indicate when we're in the Heroku environment.
        This is mostly used to modify settings for the deployed project.
        """

        # Skip this entirely when unit testing.
        if self.sd.local_test:
            return

        self.sd.write_output("  Setting Heroku environment variable...")
        cmd = 'heroku config:set ON_HEROKU=1'
        output = self.sd.execute_subp_run(cmd)
        self.sd.write_output(output)
        self.sd.write_output("    Set ON_HEROKU=1.")
        self.sd.write_output("    This is used to define Heroku-specific settings.")


    def _get_heroku_settings(self):
        """Get any heroku-specific settings that are already in place.
        """
        # If any heroku settings have already been written, we don't want to
        #  add them again. This assumes a section at the end, starting with a
        #  check for 'ON_HEROKU' in os.environ.

        with open(self.sd.settings_path) as f:
            settings_lines = f.readlines()

        self.found_heroku_settings = False
        self.current_heroku_settings_lines = []
        for line in settings_lines:
            if "if 'ON_HEROKU' in os.environ:" in line:
                self.found_heroku_settings = True
            if self.found_heroku_settings:
                self.current_heroku_settings_lines.append(line)


    def _generate_procfile(self):
        """Create Procfile, if none present."""

        #   Procfile should be in project root, if present.
        self.sd.write_output(f"\n  Looking in {self.sd.git_path} for Procfile...")
        procfile_present = 'Procfile' in os.listdir(self.sd.git_path)

        if procfile_present:
            self.sd.write_output("    Found existing Procfile.")
        else:
            self.sd.write_output("    No Procfile found. Generating Procfile...")
            if self.sd.nested_project:
                proc_command = f"web: gunicorn {self.sd.project_name}.{self.sd.project_name}.wsgi --log-file -"
            else:
                proc_command = f"web: gunicorn {self.sd.project_name}.wsgi --log-file -"

            with open(f"{self.sd.git_path}/Procfile", 'w') as f:
                f.write(proc_command)

            self.sd.write_output("    Generated Procfile with following process:")
            self.sd.write_output(f"      {proc_command}")


    def _add_gunicorn(self):
        """Add gunicorn to project requirements."""
        self.sd.write_output("\n  Looking for gunicorn...")

        if self.sd.using_req_txt:
            self.sd._add_req_txt_pkg('gunicorn')
        elif self.sd.using_pipenv:
            self.sd._add_pipenv_pkg('gunicorn')


    def _check_allowed_hosts(self):
        """Make sure project can be served from heroku."""
        # This method is specific to Heroku.

        self.sd.write_output("\n  Making sure project can be served from Heroku...")
        heroku_host = f"{self.heroku_app_name}.herokuapp.com"

        if heroku_host in settings.ALLOWED_HOSTS:
            self.sd.write_output(f"    Found {heroku_host} in ALLOWED_HOSTS.")
        elif 'herokuapp.com' in settings.ALLOWED_HOSTS:
            # This is a generic entry that allows serving from any heroku URL.
            self.sd.write_output("    Found 'herokuapp.com' in ALLOWED_HOSTS.")
        else:
            new_setting = f"ALLOWED_HOSTS.append('{heroku_host}')"
            msg_added = f"    Added {heroku_host} to ALLOWED_HOSTS for the deployed project."
            msg_already_set = f"    Found {heroku_host} in ALLOWED_HOSTS for the deployed project."
            self._add_heroku_setting(new_setting, msg_added, msg_already_set)


    def _configure_db(self):
        """Add required db-related packages, and modify settings for Heroku db.
        """
        self.sd.write_output("\n  Configuring project for Heroku database...")
        self._add_db_packages()
        self._add_db_settings()


    def _add_db_packages(self):
        """Add packages required for the Heroku db."""
        self.sd.write_output("    Adding db-related packages...")

        # psycopg2 2.9 causes "database connection isn't set to UTC" issue.
        #   See: https://github.com/ehmatthes/heroku-buildpack-python/issues/31
        if self.sd.using_req_txt:
            self.sd._add_req_txt_pkg('psycopg2<2.9')
            self.sd._add_req_txt_pkg('dj-database-url')
        elif self.sd.using_pipenv:
            self.sd._add_pipenv_pkg('psycopg2', version="<2.9")
            self.sd._add_pipenv_pkg('dj-database-url')


    def _add_db_settings(self):
        """Add settings for Heroku db."""
        self.sd.write_output("   Checking Heroku db settings...")

        # Import dj-database-url.
        new_setting = "import dj_database_url"
        msg_added = "    Added import statement for dj-database-url."
        msg_already_set = "    Found import statement for dj-database-url."
        self._add_heroku_setting(new_setting, msg_added, msg_already_set)

        # Configure db.
        new_setting = "DATABASES = {'default': dj_database_url.config(default='postgres://localhost')}"
        msg_added = "    Added setting to configure Postgres on Heroku."
        msg_already_set = "    Found setting to configure Postgres on Heroku."
        self._add_heroku_setting(new_setting, msg_added, msg_already_set)


    def _configure_static_files(self):
        """Configure static files for Heroku deployment."""

        self.sd.write_output("\n  Configuring static files for Heroku deployment...")

        # Add whitenoise to requirements.
        self.sd.write_output("    Adding staticfiles-related packages...")
        if self.sd.using_req_txt:
            self.sd._add_req_txt_pkg('whitenoise')
        elif self.sd.using_pipenv:
            self.sd._add_pipenv_pkg('whitenoise')

        # Modify settings, and add a directory for static files.
        self._add_static_file_settings()
        self._add_static_file_directory()


    def _add_static_file_settings(self):
        """Add all settings needed to manage static files."""
        self.sd.write_output("    Configuring static files settings...")

        new_setting = "STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')"
        msg_added = "    Added STATIC_ROOT setting for Heroku."
        msg_already_set = "    Found STATIC_ROOT setting for Heroku."
        self._add_heroku_setting(new_setting, msg_added, msg_already_set)

        new_setting = "STATIC_URL = '/static/'"
        msg_added = "    Added STATIC_URL setting for Heroku."
        msg_already_set = "    Found STATIC_URL setting for Heroku."
        self._add_heroku_setting(new_setting, msg_added, msg_already_set)

        new_setting = "STATICFILES_DIRS = (os.path.join(BASE_DIR, 'static'),)"
        msg_added = "    Added STATICFILES_DIRS setting for Heroku."
        msg_already_set = "    Found STATICFILES_DIRS setting for Heroku."
        self._add_heroku_setting(new_setting, msg_added, msg_already_set)


    def _add_static_file_directory(self):
        """Create a folder for static files, if it doesn't already exist.
        """
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
        with open(placeholder_file, 'w') as f:
            f.write("This is a placeholder file to make sure this folder is pushed to Heroku.")
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

        # When unit testing, don't set the heroku config var, but do make
        #   the change to settings.
        if not self.sd.local_test:
            self.sd.write_output("  Setting DEBUG env var...")
            cmd = 'heroku config:set DEBUG=FALSE'
            output = self.sd.execute_subp_run(cmd)
            self.sd.write_output(output)
            self.sd.write_output("    Set DEBUG config variable to FALSE.")

        # Modify settings to use the DEBUG config variable.
        new_setting = "DEBUG = os.getenv('DEBUG') == 'TRUE'"
        msg_added = "    Added DEBUG setting for Heroku."
        msg_already_set = "    Found DEBUG setting for Heroku."
        self._add_heroku_setting(new_setting, msg_added, msg_already_set)


    def _configure_secret_key(self):
        """Use an env var to manage the secret key."""
        # Generate a new key.
        if self.sd.on_windows:
            # Non-alphanumeric keys have been problematic on Windows.
            new_secret_key = get_random_string(length=50,
                    allowed_chars='abcdefghijklmnopqrstuvwxyz0123456789')
        else:
            new_secret_key = get_random_secret_key()

        # Set the new key as an env var on Heroku.
        #   Skip when unit testing.
        if not self.sd.local_test:
            self.sd.write_output("  Setting new secret key for Heroku...")
            cmd = f"heroku config:set SECRET_KEY={new_secret_key}"
            output = self.sd.execute_subp_run(cmd)
            self.sd.write_output(output)
            self.sd.write_output("    Set SECRET_KEY config variable.")

        # Modify settings to use the env var's value as the secret key.
        new_setting = "SECRET_KEY = os.getenv('SECRET_KEY')"
        msg_added = "    Added SECRET_KEY setting for Heroku."
        msg_already_set = "    Found SECRET_KEY setting for Heroku."
        self._add_heroku_setting(new_setting, msg_added, msg_already_set)


    def _conclude_automate_all(self):
        """Finish automating the push to Heroku."""
        if not self.sd.automate_all:
            return

        self.sd.write_output("\n\nCommitting and pushing project...")

        self.sd.write_output("  Adding changes...")
        cmd = 'git add .'
        output = self.sd.execute_subp_run(cmd)
        self.sd.write_output(output)
        self.sd.write_output("  Committing changes...")
        # If we write this command as a string, the commit message will be split
        #   incorrectly.
        cmd_parts = ['git', 'commit', '-am', '"Configured project for deployment."']
        output = self.sd.execute_subp_run_parts(cmd_parts)
        self.sd.write_output(output)

        self.sd.write_output("  Pushing to heroku...")

        # Get the current branch name. Get the first line of status output,
        #   and keep everything after "On branch ".
        cmd = 'git status'
        git_status = self.sd.execute_subp_run(cmd)
        self.sd.write_output(git_status)
        status_str = git_status.stdout.decode()
        self.current_branch = status_str.split('\n')[0][10:]

        # Push current local branch to Heroku main branch.
        # This process usually takes a minute or two, which is longer than we
        #   want users to wait for console output. So rather than capturing
        #   output with subprocess.run(), we use Popen and stream while logging.
        # DEV: Note that the output of `git push heroku` goes to stderr, not stdout.
        self.sd.write_output(f"    Pushing branch {self.current_branch}...")
        if self.current_branch in ('main', 'master'):
            cmd = f"git push heroku {self.current_branch}"
        else:
            cmd = f"git push heroku {self.current_branch}:main"
        self.sd.execute_command(cmd)

        # Run initial set of migrations.
        self.sd.write_output("  Migrating deployed app...")
        if self.sd.nested_project:
            cmd = f"heroku run python {self.sd.project_name}/manage.py migrate"
        else:
            cmd = 'heroku run python manage.py migrate'
        output = self.sd.execute_subp_run(cmd)

        self.sd.write_output(output)

        # Open Heroku app, so it simply appears in user's browser.
        self.sd.write_output("  Opening deployed app in a new browser tab...")
        cmd = 'heroku open'
        output = self.sd.execute_subp_run(cmd)
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
            msg = dh_msgs.success_msg_automate_all(self.heroku_app_name,
                    self.current_branch)
        else:
            # Show steps to finish the deployment process.
            msg = dh_msgs.success_msg(self.sd.using_pipenv, self.heroku_app_name)

        self.sd.write_output(msg)


    # --- Utility methods ---

    def _check_current_heroku_settings(self, heroku_setting):
        """Check if a setting has already been defined in the heroku-specific
        settings section.
        """
        return any(heroku_setting in line for line in self.current_heroku_settings_lines)


    def _add_heroku_setting(self, new_setting, msg_added='',
            msg_already_set=''):
        """Add a new setting to the heroku-specific settings, if not already
        present.
        """
        already_set = self._check_current_heroku_settings(new_setting)
        if not already_set:
            with open(self.sd.settings_path, 'a') as f:
                self._prep_heroku_setting(f)
                f.write(f"\n    {new_setting}")
                self.sd.write_output(msg_added)
        else:
            self.sd.write_output(msg_already_set)


    def _prep_heroku_setting(self, f_settings):
        """Add a block for Heroku-specific settings, if it doesn't already
        exist.
        """
        if not self.found_heroku_settings:
            # DEV: Should check if `import os` already exists in settings file.
            f_settings.write("\nimport os")
            f_settings.write("\nif 'ON_HEROKU' in os.environ:")

            # Won't need to add these lines anymore.
            self.found_heroku_settings = True

    def _generate_summary(self):
        """Generate the friendly summary, which is html for now."""
        # Generate the summary file.
        path = self.sd.log_dir_path / 'deployment_summary.html'

        summary_str = "<h2>Understanding your deployment</h2>"
        path.write_text(summary_str)

        msg = f"\n  Generated friendly summary: {path}"
        self.sd.write_output(msg)
