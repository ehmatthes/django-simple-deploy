"""Manages all Heroku-specific aspects of the deployment process."""

import sys, os, re, subprocess

from django.conf import settings
from django.core.management.base import CommandError

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
        self.stdout.write("Configuring project for deployment to Heroku...")

        self._prep_automate_all()
        self._get_heroku_app_info()
        self._set_heroku_env_var()
        self._inspect_project()
        self.sd._add_simple_deploy_req()
        self._generate_procfile()
        self._add_gunicorn()
        self._check_allowed_hosts()
        self._configure_db()
        self._configure_static_files()
        self._conclude_automate_all()
        self._show_success_message()


    def _prep_automate_all(self):
        """Do intial work for automating entire process."""
        # This is platform-specific, because we want to specify exactly what
        #   will be automated.

        # Skip this prep work if --automate-all not used.
        if not self.sd.automate_all:
            return

        # Confirm the user knows exactly what will be automated.
        self.stdout.write(dh_msgs.confirm_automate_all)

        # Get confirmation.
        confirmed = ''
        while confirmed.lower() not in ('y', 'yes', 'n', 'no'):
            prompt = "\nAre you sure you want to do this? (yes|no) "
            confirmed = input(prompt)
            if confirmed.lower() not in ('y', 'yes', 'n', 'no'):
                self.stdout.write("  Please answer yes or no.")

        if confirmed.lower() in ('y', 'yes'):
            self.stdout.write("  Running `heroku create`...")
            subprocess.run(['heroku', 'create'])
        else:
            # Quit and have the user run the command again; don't assume not
            #   wanting to automate means they want to configure.
            self.stdout.write(d_msgs.cancel_automate_all)
            sys.exit()


    def _get_heroku_app_info(self):
        """Get info about the Heroku app we're pushing to."""
        # We assume the user has already run 'heroku create', or --automate-all
        #   has run it. If it hasn't been run, we'll quit and tell them to do so.
        self.stdout.write("  Inspecting Heroku app...")
        apps_info = subprocess.run(["heroku", "apps:info"], capture_output=True)

        # Turn stdout info into a list of strings that we can then parse.
        #   If no app exists, stdout is empty and the output went to stderr.
        apps_info = apps_info.stdout.decode().split('\n')
        # DEV: Use this code when we can require Python >=3.9.
        # self.heroku_app_name = apps_info[0].removeprefix('=== ')
        self.heroku_app_name = apps_info[0].replace('=== ', '')

        if self.heroku_app_name:
            self.stdout.write(f"    Found Heroku app: {self.heroku_app_name}")
        else:
            # Let user know they need to run `heroku create`.
            raise CommandError(dh_msgs.no_heroku_app_detected)


    def _set_heroku_env_var(self):
        """Set a config var to indicate when we're in the Heroku environment.
        This is mostly used to modify settings for the deployed project.
        """
        self.stdout.write("  Setting Heroku environment variable...")
        subprocess.run(["heroku", "config:set", "ON_HEROKU=1"])
        self.stdout.write("    Set ON_HEROKU=1.")
        self.stdout.write("    This is used to define Heroku-specific settings.")


    def _inspect_project(self):
        """Inspect the project, and pull information needed by multiple steps.
        """

        # Get platform-agnostic information about the project.
        self.sd._inspect_project()

        self._get_heroku_settings()


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
        self.stdout.write(f"\n  Looking in {self.sd.project_root} for Procfile...")
        procfile_present = 'Procfile' in os.listdir(self.sd.project_root)

        if procfile_present:
            self.stdout.write("    Found existing Procfile.")
        else:
            self.stdout.write("    No Procfile found. Generating Procfile...")
            proc_command = f"web: gunicorn {self.sd.project_name}.wsgi --log-file -"

            with open(f"{self.sd.project_root}/Procfile", 'w') as f:
                f.write(proc_command)

            self.stdout.write("    Generated Procfile with following process:")
            self.stdout.write(f"      {proc_command}")


    def _add_gunicorn(self):
        """Add gunicorn to project requirements."""
        self.stdout.write("\n  Looking for gunicorn...")

        if self.sd.using_req_txt:
            self.sd._add_req_txt_pkg('gunicorn')
        elif self.sd.using_pipenv:
            self.sd._add_pipenv_pkg('gunicorn')


    def _check_allowed_hosts(self):
        """Make sure project can be served from heroku."""
        # This method is specific to Heroku, but the error message is not.

        self.stdout.write("\n  Making sure project can be served from Heroku...")
        heroku_host = f"{self.heroku_app_name}.herokuapp.com"

        if heroku_host in settings.ALLOWED_HOSTS:
            self.stdout.write(f"    Found {heroku_host} in ALLOWED_HOSTS.")
        elif 'herokuapp.com' in settings.ALLOWED_HOSTS:
            # This is a generic entry that allows serving from any heroku URL.
            self.stdout.write("    Found 'herokuapp.com' in ALLOWED_HOSTS.")
        elif not settings.ALLOWED_HOSTS:
            new_setting = f"ALLOWED_HOSTS.append('{heroku_host}')"
            msg_added = f"    Added {heroku_host} to ALLOWED_HOSTS for the deployed project."
            msg_already_set = f"    Found {heroku_host} in ALLOWED_HOSTS for the deployed project."
            self._add_heroku_setting(new_setting, msg_added, msg_already_set)
        else:
            # Let user know there's a nonempty ALLOWED_HOSTS, that doesn't 
            #   contain the current Heroku URL.
            msg = d_msgs.allowed_hosts_not_empty_msg(heroku_host)
            raise CommandError(msg)


    def _configure_db(self):
        """Add required db-related packages, and modify settings for Heroku db.
        """
        self.stdout.write("\n  Configuring project for Heroku database...")
        self._add_db_packages()
        self._add_db_settings()


    def _add_db_packages(self):
        """Add packages required for the Heroku db."""
        self.stdout.write("    Adding db-related packages...")

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
        self.stdout.write("   Checking Heroku db settings...")

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

        self.stdout.write("\n  Configuring static files for Heroku deployment...")

        # Add whitenoise to requirements.
        self.stdout.write("    Adding staticfiles-related packages...")
        if self.sd.using_req_txt:
            self.sd._add_req_txt_pkg('whitenoise')
        elif self.sd.using_pipenv:
            self.sd._add_pipenv_pkg('whitenoise')

        # Modify settings, and add a directory for static files.
        self._add_static_file_settings()
        self._add_static_file_directory()


    def _add_static_file_settings(self):
        """Add all settings needed to manage static files."""
        self.stdout.write("    Configuring static files settings...")

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
        self.stdout.write("    Checking for static files directory...")

        # Make sure there's a static files directory.
        static_files_dir = f"{self.sd.project_root}/static"
        if os.path.exists(static_files_dir):
            if os.listdir(static_files_dir):
                self.stdout.write("    Found non-empty static files directory.")
                return
        else:
            os.makedirs(static_files_dir)
            self.stdout.write("    Created empty static files directory.")

        # Add a placeholder file to the empty static files directory.
        placeholder_file = f"{static_files_dir}/placeholder.txt"
        with open(placeholder_file, 'w') as f:
            f.write("This is a placeholder file to make sure this folder is pushed to Heroku.")
        self.stdout.write("    Added placeholder file to static files directory.")


    def _conclude_automate_all(self):
        """Finish automating the push to Heroku."""
        if not self.sd.automate_all:
            return

        self.stdout.write("\n\nCommitting and pushing project...")

        self.stdout.write("  Adding changes...")
        subprocess.run(['git', 'add', '.'])
        self.stdout.write("  Committing changes...")
        subprocess.run(['git', 'commit', '-am', '"Configured project for deployment."'])

        self.stdout.write("  Pushing to heroku...")

        # Get the current branch name. Get the first line of status output,
        #   and keep everything after "On branch ".
        git_status = subprocess.run(['git', 'status'], capture_output=True, text=True)
        self.current_branch = git_status.stdout.split('\n')[0][10:]

        # Push current local branch to Heroku main branch.
        self.stdout.write(f"    Pushing branch {self.current_branch}...")
        if self.current_branch in ('main', 'master'):
            subprocess.run(['git', 'push', 'heroku', self.current_branch])
        else:
            subprocess.run(['git', 'push', 'heroku', f'{self.current_branch}:main'])

        # Run initial set of migrations.
        self.stdout.write("  Migrating deployed app...")
        subprocess.run(['heroku', 'run', 'python', 'manage.py', 'migrate'])

        # Open Heroku app, so it simply appears in user's browser.
        self.stdout.write("  Opening deployed app in a new browser tab...")
        subprocess.run(['heroku', 'open'])


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

        self.stdout.write(msg)


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
                self.stdout.write(msg_added)
        else:
            self.stdout.write(msg_already_set)


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