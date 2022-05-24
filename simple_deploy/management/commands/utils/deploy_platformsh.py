"""Manages all platform.sh-specific aspects of the deployment process."""

# Note: All public-facing references to platform.sh will include a dot, dash, or
#  underscore, ie platform_sh.
#  Internally, we won't use a space, ie platformsh or plsh.

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

        self._add_platformsh_settings()

        # DEV: Group this with later yaml generation methods.
        self._generate_platform_app_yaml()

        # DEV: These can be done in one pass.
        self._add_platformshconfig()
        self._add_gunicorn()
        self._add_psycopg2()

        # DEV: These could be refactored.
        self._make_platform_dir()
        self._generate_routes_yaml()
        self._generate_services_yaml()

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


    def _add_platformsh_settings(self):
        """Add platformsh-specific settings."""
        # The only project-specific setting is the ALLOWED_HOSTS; that makes
        #   modifying settings *much* easier than for other platforms.
        #   Just check if the settings are present, and if not, dump them in.

        # DEV: Modify this to make a more specific ALLOWED_HOSTS entry.
        #   For now, at proof of concept stage, it's just '*'.

        self.sd.write_output("\n  Checking if platform.sh-specific settings present in settings.py...")

        with open(self.sd.settings_path) as f:
            settings_string = f.read()

        if 'if config.is_valid_platform():' in settings_string:
            self.sd.write_output("\n    Found platform.sh settings block in settings.py.")
            return

        # Add platformsh settings block.
        # This comes from a template, which will make it easier to modify things
        #   like ALLOWED_HOSTS. This approach may work better for other platforms
        #   as well.
        self.sd.write_output("    No platform.sh settings found in settings.py; adding settings...")
        my_loader = Loader(Engine.get_default())
        my_template = my_loader.get_template('platformsh_settings.py')

        # Build context dict for template.
        safe_settings_string = mark_safe(settings_string)
        context = {'current_settings': safe_settings_string}
        template_string = render_to_string('platformsh_settings.py', context)

        path = Path(self.sd.settings_path)
        path.write_text(template_string)

        msg = f"    Modified settings.py file: {path}"
        self.sd.write_output(msg)


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

        self.sd.write_output(plsh_msgs.success_msg)

