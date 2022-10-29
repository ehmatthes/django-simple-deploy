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
        self.sd.write_output("Configuring project for deployment to Platform.sh...")

        self._add_platformsh_settings()

        # DEV: Group this with later yaml generation methods.
        self._generate_platform_app_yaml()

        # DEV: These can be done in one pass.
        self._add_platformshconfig()
        self._add_gunicorn()
        self._add_psycopg2()

        # DEV: These could be refactored.
        self._make_platform_dir()
        self._generate_services_yaml()

        self._conclude_automate_all()

        self._show_success_message()


    # --- Methods used in this class ---

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
        #  check for `if config.is_valid_platform():`

        with open(self.sd.settings_path) as f:
            settings_lines = f.readlines()

        self.found_platformsh_settings = False
        self.current_platformsh_settings_lines = []
        for line in settings_lines:
            if "if config.is_valid_platform():" in line:
                self.found_platformsh_settings = True
            if self.found_platformsh_settings:
                self.current_platformsh_settings_lines.append(line)


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
            context = {
                'project_name': self.sd.project_name, 
                'deployed_project_name': self.deployed_project_name
                }
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
            self.sd.add_req_txt_pkg('platformshconfig')
        elif self.sd.using_pipenv:
            self.sd.add_pipenv_pkg('platformshconfig')


    def _add_gunicorn(self):
        """Add gunicorn to project requirements."""
        self.sd.write_output("\n  Looking for gunicorn...")

        if self.sd.using_req_txt:
            self.sd.add_req_txt_pkg('gunicorn')
        elif self.sd.using_pipenv:
            self.sd.add_pipenv_pkg('gunicorn')


    def _add_psycopg2(self):
        """Add psycopg2 to project requirements."""
        self.sd.write_output("\n  Looking for psycopg2...")

        if self.sd.using_req_txt:
            self.sd.add_req_txt_pkg('psycopg2')
        elif self.sd.using_pipenv:
            self.sd.add_pipenv_pkg('psycopg2')


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


    def _generate_services_yaml(self):
        """Generate the .platform/services.yaml file, if not present."""
        
        # File should be in self.platform_dir_path, if present.
        self.sd.write_output(f"\n  Looking in {self.platform_dir_path} for services.yaml file...")
        services_yaml_present = 'services.yaml' in os.listdir(self.platform_dir_path)

        if services_yaml_present:
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


    def _conclude_automate_all(self):
        """Finish automating the push to Platform.sh.
        - Commit all changes.
        - Call `platform push`.
        - Open project.
        """
        # Making this check here lets deploy() be cleaner.
        if not self.sd.automate_all:
            return

        self.sd.commit_changes()

        # Push project.
        # Use execute_command(), to stream the output as it runs.
        self.sd.write_output("  Pushing to Platform.sh...")
        cmd = "platform push --yes"
        self.sd.execute_command(cmd)

        # Open project.
        self.sd.write_output("  Opening deployed app in a new browser tab...")
        cmd = "platform url --yes"
        output = self.sd.execute_subp_run(cmd)
        self.sd.write_output(output)

        # Get url of deployed project.
        #   This can be done with an re, but there's one line of output with
        #   a url, so finding that line is simpler.
        self.deployed_url = ''
        for line in output.stdout.decode().split('\n'):
            if 'https' in line:
                self.deployed_url = line.strip()


    def _show_success_message(self):
        """After a successful run, show a message about what to do next."""

        # DEV:
        # - Mention that this script should not need to be run again, unless
        #   creating a new deployment.
        #   - Describe ongoing approach of commit, push, migrate. Lots to consider
        #     when doing this on production app with users, make sure you learn.

        if self.sd.automate_all:
            msg = plsh_msgs.success_msg_automate_all(self.deployed_url)
            self.sd.write_output(msg)
        else:
            msg = plsh_msgs.success_msg(self.sd.log_output)
            self.sd.write_output(msg)


    # --- Methods called from simple_deploy.py ---

    def confirm_preliminary(self):
        """Deployment to platform.sh is in a preliminary state, and we need to be
        explicit about that.
        """
        # Skip this confirmation when unit testing.
        if self.sd.unit_testing:
            return

        self.stdout.write(plsh_msgs.confirm_preliminary)
        confirmed = self.sd.get_confirmation(skip_logging=True)

        if confirmed:
            self.stdout.write("  Continuing with platform.sh deployment...")
        else:
            # Quit and invite the user to try another platform.
            # We are happily exiting the script; there's no need to raise a
            #   CommandError.
            self.stdout.write(plsh_msgs.cancel_plsh)
            sys.exit()


    def validate_platform(self):
        """Make sure the local environment and project supports deployment to
        Platform.sh.
        
        The returncode for a successful command is 0, so anything truthy means
          a command errored out.
        """
        self._validate_cli()
        self._validate_platformshconfig()

        # When running unit tests, will not be logged into CLI.
        if not self.sd.unit_testing:
            self.deployed_project_name = self._get_platformsh_project_name()
            self.org_name = self._get_org_name()
        else:
            self.deployed_project_name = self.sd.deployed_project_name


    def prep_automate_all(self):
        """Do intial work for automating entire process.
        We know from validate_project() that user is logged into CLI.
        
        Returns:
        - None if creation was successful.
        - Raises CommandError if create command fails.

        Note: create command outputs project id to stdout if known, all other
          output goes to stderr.
        """

        self.sd.write_output("  Running `platform create`...")
        self.sd.write_output("    (Please be patient, this can take a few minutes.")
        cmd = f'platform create --title { self.deployed_project_name } --org {self.org_name} --region {self.sd.region} --yes'

        try:
            # Include check=True in this call, so we can process more
            #   significant errors that can come out of this call.
            # For example, if user can't create a project the 
            #   returncode will be 6, not 1. That causes subprocess.run()
            #   to actually raise an exception, not just pass a CompletedProcess
            #   instance.
            output = self.sd.execute_subp_run(cmd, check=True)
        except subprocess.CalledProcessError as e:
            error_msg = plsh_msgs.unknown_create_error(e)
            raise CommandError(error_msg)

        self.sd.write_output(output)


    # --- Helper methods for methods called from simple_deploy.py ---

    def _validate_cli(self):
        """Make sure the Platform.sh CLI is installed."""
        cmd = 'platform --version'
        output_obj = self.sd.execute_subp_run(cmd)
        if output_obj.returncode:
            raise CommandError(plsh_msgs.cli_not_installed)


    def _validate_platformshconfig(self):
        """If not using automate-all, make sure platformshconfig is installed
        locally.
        """
        if not self.sd.automate_all:
            cmd = 'pip show platformshconfig'
            output_obj = self.sd.execute_subp_run(cmd)
            if output_obj.returncode:
                raise CommandError(plsh_msgs.platformshconfig_not_installed)


    def _get_platformsh_project_name(self):
        """Get the deployed project name.
        This is the name that was given in the `platform create` command.
        - Try to get this from `project:info`.
        - If can't get project name:
          - Exit with warning, and inform user of --deployed-project-name
            flag to override this error.
        """
        # If we're creating the project, we'll just use the startprojet name.
        if self.sd.automate_all:
            return self.sd.project_name

        # Use the provided name if --deployed-project-name specified.
        if self.sd.deployed_project_name:
            return self.sd.deployed_project_name

        # Use --yes flag to avoid interactive prompt hanging in background
        #   if the user is not currently logged in to the CLI.
        cmd = "platform project:info --yes"
        output_obj = self.sd.execute_subp_run(cmd)
        output_str = output_obj.stdout.decode()

        # If there's no stdout, the user is probably logged out, hasn't called
        #   create, or doesn't have the CLI installed.
        # Also, I've seen both ProjectNotFoundException and RootNotFoundException
        #   raised when no project has been created.
        if not output_str:
            output_str = output_obj.stderr.decode()
            if 'LoginRequiredException' in output_str:
                raise CommandError(plsh_msgs.login_required)
            elif 'ProjectNotFoundException' in output_str:
                raise CommandError(plsh_msgs.no_project_name)
            elif 'RootNotFoundException' in output_str:
                raise CommandError(plsh_msgs.no_project_name)
            else:
                error_msg = plsh_msgs.unknown_error
                error_msg += plsh_msgs.cli_not_installed
                raise CommandError(error_msg)

        # Pull deployed project name from output.
        deployed_project_name_re = r'(\| title\s+?\|\s*?)(.*?)(\s*?\|)'
        match = re.search(deployed_project_name_re, output_str)
        if match:
            return match.group(2).strip()
        
        # Couldn't find a project name. Warn user, and let them know
        #   about override flag.
        raise CommandError(plsh_msgs.no_project_name)


    def _get_org_name(self):
        """Get the organization name associated with the user's Platform.sh
        account. This is needed for creating a project using automate_all.

        Confirm that it's okay to use this org.

        Returns:
        - None if not using automate-all.
        - String containing org name if found, and confirmed.
        - Raises CommandError if org name found, but not confirmed.
        - Raises CommandError with msg if CLI login required.
        - Raises CommandError with msg if org name not found.
        """
        if not self.sd.automate_all:
            return

        # Use --yes to suppress hanging at login prompt.
        cmd = "platform organization:list --yes"
        output_obj = self.sd.execute_subp_run(cmd)
        output_str = output_obj.stdout.decode()

        if not output_str:
            output_str = output_obj.stderr.decode()
            if 'LoginRequiredException' in output_str:
                raise CommandError(plsh_msgs.login_required)
            else:
                error_msg = plsh_msgs.unknown_error
                error_msg += plsh_msgs.cli_not_installed
                raise CommandError(error_msg)

        # Pull org name from output. Start by removing line containing lables.
        output_str_lines = [line for line in output_str.split("\n") if "Owner email" not in line]
        modified_output_str = '\n'.join(output_str_lines)
        org_name_re = r'(\|\s*)([a-zA-Z_]*)(.*)'
        match = re.search(org_name_re, modified_output_str)
        if match:
            org_name = match.group(2).strip()
            if self._confirm_use_org_name(org_name):
                return org_name
        else:
            # Got stdout, but can't find org id. Unknown error.
            raise CommandError(plsh_msgs.org_not_found)


    def _confirm_use_org_name(self, org_name):
        """Confirm that it's okay to use the org name that was found.
        Returns:
        - True if confirmed.
        - sys.exit() if not confirmed.
        """

        self.stdout.write(plsh_msgs.confirm_use_org_name(org_name))
        confirmed = self.sd.get_confirmation(skip_logging=True)

        if confirmed:
            self.stdout.write("  Okay, continuing with deployment.")
            return True
        else:
            # Exit, with a message that configuration is still an option.
            msg = plsh_msgs.cancel_plsh
            msg += plsh_msgs.may_configure
            raise CommandError(msg)
