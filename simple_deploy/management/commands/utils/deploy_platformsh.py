"""Manages all platform.sh-specific aspects of the deployment process."""

# Note: All public-facing references to platform.sh will include a dot, dash, or
#  underscore, ie platform_sh.
#  Internally, we won't use a space, ie platformsh or plsh.

import sys, os, re, subprocess

from django.conf import settings
from django.core.management.base import CommandError
from django.core.management.utils import get_random_secret_key
from django.utils.crypto import get_random_string
from django.template.engine import Engine
from django.template.loaders.app_directories import Loader
from django.template.loader import render_to_string

from simple_deploy.management.commands.utils import deploy_messages as d_msgs
from simple_deploy.management.commands.utils import deploy_messages_platformsh as plsh_msgs


class PlatformshDeployer:
    """Perform the initial deployment of a simple project.
    Configure as much as possible automatically.
    """

    def __init__(self, command):
        """Establishes connection to existing simple_deploy command object."""
        self.sd = command
        self.stdout = self.sd.stdout


    def deploy(self, *args, **options):
        self.sd.write_output("Configuring project for deployment to platform.sh...")

        self._confirm_preliminary()
        self.sd._add_simple_deploy_req()
        self._get_platformsh_settings()

        # DEV: Group this with later yaml generation methods.
        self._generate_platform_app_yaml()

        # DEV: These can be done in one pass.
        self._add_platformshconfig()
        self._add_gunicorn()
        self._add_psycopg2()

        self._check_allowed_hosts()
        
        # DEV: These could be refactored.
        self._make_platform_dir()
        self._generate_routes_yaml()
        self._generate_services_yaml()

        sys.exit()


        self._configure_db()
        self._configure_static_files()
        self._configure_debug()
        self._configure_secret_key()
        self._conclude_automate_all()
        self._summarize_deployment()
        self._show_success_message()


    def _confirm_preliminary(self):
        """Deployment to platform.sh is in a preliminary state, and we need to be
        explicit about that.
        """
        # DEV: Much of this logic can be pulled into simple_deploy; it's used
        #   by any experimental Deployer class.
        self.stdout.write(plsh_msgs.confirm_preliminary)

        # Get confirmation.
        confirmed = ''
        while confirmed.lower() not in ('y', 'yes', 'n', 'no'):
            prompt = "\nAre you sure you want to continue deploying to platform.sh? (yes|no) "
            confirmed = input(prompt)
            if confirmed.lower() not in ('y', 'yes', 'n', 'no'):
                self.stdout.write("  Please answer yes or no.")

        if confirmed.lower() in ('y', 'yes'):
            self.stdout.write("  Continuing with platform.sh deployment...")
        else:
            # Quit and invite the user to try another platform.
            self.stdout.write(plsh_msgs.cancel_plsh)
            sys.exit()


    def _get_platformsh_settings(self):
        """Get any platformsh-specific settings that are already in place.
        """
        # If any platformsh settings have already been written, we don't want to
        #  add them again. This assumes a section at the end, starting with a
        #  check for 'ON_HEROKU' in os.environ.

        with open(self.sd.settings_path) as f:
            settings_lines = f.readlines()

        self.found_platformsh_settings = False
        self.current_platformsh_settings_lines = []
        for line in settings_lines:
            if "if config.is_valid_platform():" in line:
                self.found_platformsh_settings = True
            if self.found_platformsh_settings:
                self.current_platformsh_settings_lines.append(line)

        # DEV: Remove these lines.
        print('--- platformsh settings: ---')
        print(self.current_platformsh_settings_lines)


    def _generate_platform_app_yaml(self):
        """Create .platform.app.yaml file, if not present."""

        # File should be in project root, if present.
        self.sd.write_output(f"\n  Looking in {self.sd.git_path} for .platform.app.yaml file...")
        p_app_yaml_present = '.platform.app.yaml' in os.listdir(self.sd.git_path)

        if p_app_yaml_present:
            self.sd.write_output("    Found existing .platform.app.yaml file.")
        else:
            # Generate file from template.
            self.sd.write_output("    No .platform.app.yaml file found. Generating file...")
            my_loader = Loader(Engine.get_default())
            my_template = my_loader.get_template('platform.app.yaml')

            # Build context dict for template.
            context = {'project_name': self.sd.project_name}
            template_string = render_to_string('platform.app.yaml', context)

            path = self.sd.project_root / '.platform.app.yaml'
            path.write_text(template_string)

            msg = f"\n    Generated .platform.app.yaml file: {path}"
            self.sd.write_output(msg)
            return path


    def _add_platformshconfig(self):
        """Add platformshconfig to project requirements."""
        self.sd.write_output("\n  Looking for platformshconfig...")

        if self.sd.using_req_txt:
            self.sd._add_req_txt_pkg('platformshconfig')
        elif self.sd.using_pipenv:
            self.sd._add_pipenv_pkg('platformshconfig')


    def _add_gunicorn(self):
        """Add gunicorn to project requirements."""
        self.sd.write_output("\n  Looking for gunicorn...")

        if self.sd.using_req_txt:
            self.sd._add_req_txt_pkg('gunicorn')
        elif self.sd.using_pipenv:
            self.sd._add_pipenv_pkg('gunicorn')


    def _add_psycopg2(self):
        """Add psycopg2 to project requirements."""
        self.sd.write_output("\n  Looking for psycopg2...")

        if self.sd.using_req_txt:
            self.sd._add_req_txt_pkg('psycopg2')
        elif self.sd.using_pipenv:
            self.sd._add_pipenv_pkg('psycopg2')


    def _check_allowed_hosts(self):
        """Make sure project can be served from platformsh."""
        # This method is specific to platformsh.

        self.sd.write_output("\n  Making sure project can be served from platform.sh...")

        # DEV: Configure an ALLOWED_HOSTS entry that's specific to this deployment.
        # Use '*' for now, to focus on more specific aspects of platformsh deployment.
        platformsh_host = '*'

        if platformsh_host in settings.ALLOWED_HOSTS:
            self.sd.write_output(f"    Found {platformsh_host} in ALLOWED_HOSTS.")
        else:
            new_setting = f"ALLOWED_HOSTS.append('{platformsh_host}')"
            msg_added = f"    Added {platformsh_host} to ALLOWED_HOSTS for the deployed project."
            msg_already_set = f"    Found {platformsh_host} in ALLOWED_HOSTS for the deployed project."
            self._add_platformsh_setting(new_setting, msg_added, msg_already_set)


    def _make_platform_dir(self):
        """Add a .platform directory, if it doesn't already exist."""

        # Directory should be in project root, if present.
        self.sd.write_output(f"\n  Looking in {self.sd.git_path} for .platform/ directory...")

        self.platform_dir_path = self.sd.git_path / '.platform'
        if self.platform_dir_path.exists():
            self.sd.write_output("    Found existing .platform/ directory.")
        else:
            self.platform_dir_path.mkdir()
            self.sd.write_output(f"    Made .platform directory: {self.platform_dir_path}")


    def _generate_routes_yaml(self):
        """Generate the .platform/routes.yaml file, if not present."""

        # File should be in self.platform_dir_path, if present.
        self.sd.write_output(f"\n  Looking in {self.platform_dir_path} for routes.yaml file...")
        routes_yaml_present = 'routes.yaml' in os.listdir(self.platform_dir_path)

        if routes_yaml_present:
            self.sd.write_output("    Found existing routes.yaml file.")
        else:
            # Generate file from template.
            self.sd.write_output("    No routes.yaml file found. Generating file...")
            my_loader = Loader(Engine.get_default())
            my_template = my_loader.get_template('routes.yaml')

            # Build context dict for template.
            context = {'project_name': self.sd.project_name}
            template_string = render_to_string('routes.yaml', context)

            path = self.platform_dir_path / 'routes.yaml'
            path.write_text(template_string)

            msg = f"\n    Generated routes.yaml file: {path}"
            self.sd.write_output(msg)
            return path


    def _generate_services_yaml(self):
        """Generate the .platform/services.yaml file, if not present."""
        
        # File should be in self.platform_dir_path, if present.
        self.sd.write_output(f"\n  Looking in {self.platform_dir_path} for services.yaml file...")
        routes_yaml_present = 'services.yaml' in os.listdir(self.platform_dir_path)

        if routes_yaml_present:
            self.sd.write_output("    Found existing services.yaml file.")
        else:
            # Generate file from template.
            # DEV: We're not modifying this file, so it can just be copied 
            #   from templates file to .platform/ directory.
            self.sd.write_output("    No services.yaml file found. Generating file...")
            my_loader = Loader(Engine.get_default())
            my_template = my_loader.get_template('services.yaml')

            template_string = render_to_string('services.yaml')

            path = self.platform_dir_path / 'services.yaml'
            path.write_text(template_string)

            msg = f"\n    Generated services.yaml file: {path}"
            self.sd.write_output(msg)
            return path



    # --- Utility methods ---

    def _check_current_platformsh_settings(self, platformsh_setting):
        """Check if a setting has already been defined in the platformsh-specific
        settings section.
        """
        return any(platformsh_setting in line for line in self.current_platformsh_settings_lines)


    def _add_platformsh_setting(self, new_setting, msg_added='',
            msg_already_set=''):
        """Add a new setting to the platformsh-specific settings, if not already
        present.
        """
        already_set = self._check_current_platformsh_settings(new_setting)
        if not already_set:
            with open(self.sd.settings_path, 'a') as f:
                self._prep_platformsh_setting(f)
                f.write(f"\n    {new_setting}")
                self.sd.write_output(msg_added)
        else:
            self.sd.write_output(msg_already_set)


    def _prep_platformsh_setting(self, f_settings):
        """Add a block for Platformsh-specific settings, if it doesn't already
        exist.
        """
        if not self.found_platformsh_settings:
            # DEV: Should check if `import os` already exists in settings file.
            # DEV: Use a template or block string to write this section.
            f_settings.write("\n\n# platform.sh settings")
            f_settings.write("\nimport os")
            f_settings.write("\nfrom platformshconfig import Config")
            f_settings.write("\n\n# Import some platform.sh settings from environment.")
            f_settings.write("\nconfig = Config()")
            f_settings.write("\nif config.is_valid_platform():")

            # Won't need to add these lines anymore.
            self.found_platformsh_settings = True











# ------------- OLD HEROKU STUFF ------------
# Remove after modifying for platformsh.



















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



