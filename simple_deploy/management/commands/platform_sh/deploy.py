"""Manages all platform.sh-specific aspects of the deployment process."""

# Note: All public-facing references to platform.sh will include a dot, dash, or
#  underscore, ie platform_sh.
#  Internally, we won't use a space, ie platformsh or plsh.

import sys, os, subprocess, time
from pathlib import Path

from django.conf import settings
from django.core.management.utils import get_random_secret_key
from django.utils.crypto import get_random_string
from django.utils.safestring import mark_safe

from simple_deploy.management.commands import deploy_messages as d_msgs
from simple_deploy.management.commands.platform_sh import deploy_messages as plsh_msgs

from simple_deploy.management.commands.utils import SimpleDeployCommandError
from simple_deploy.management.commands import utils as sd_utils
from simple_deploy.management.commands.platform_sh import utils as plsh_utils


class PlatformDeployer:
    """Perform the initial deployment to Platform.sh.

    If --automate-all is used, carry out an actual deployment.
    If not, do all configuration work so the user only has to commit changes, and call
    `platform push`.
    """

    def __init__(self, command):
        """Establishes connection to existing simple_deploy command object."""
        self.sd = command
        self.stdout = self.sd.stdout
        self.messages = plsh_msgs

    # --- Public methods ---

    def deploy(self, *args, **options):
        """Coordinate the overall configuration and deployment."""

        self.sd.write_output("\nConfiguring project for deployment to Platform.sh...")

        self._confirm_preliminary()

        if self.sd.automate_all:
            self._confirm_automate_all()

        self._validate_platform()

        if self.sd.automate_all:
            self._prep_automate_all()

        self._add_platformsh_settings()
        self._add_requirements()
        self._generate_platform_app_yaml()
        self._make_platform_dir()
        self._generate_services_yaml()
        self._conclude_automate_all()
        self._show_success_message()

    # --- Helper methods for deploy() ---

    def _confirm_preliminary(self):
        """Confirm acknwledgement of preliminary (pre-1.0) state of project."""
        self.sd.write_output(self.messages.confirm_preliminary)

        # Unit test check is here, so message is logged.
        if self.sd.unit_testing:
            return

        if self.sd.get_confirmation():
            self.sd.write_output("  Continuing with platform.sh deployment...")
        else:
            # Quit and invite the user to try another platform. We are happily exiting
            # the script; there's no need to raise an error.
            self.sd.write_output(self.messages.cancel_plsh)
            sys.exit()

    def _validate_platform(self):
        """Make sure the local environment and project supports deployment to
        Platform.sh.

        Make sure CLI is installed, and user is authenticated. Make sure necessary
        resources have been created and identified, and that we have the user's
        permission to use those resources.

        Returns:
            None

        Raises:
            SimpleDeployCommandError: If we find any reason deployment won't work.
        """
        if self.sd.unit_testing:
            # Unit tests don't use the CLI. Use the deployed project name that was
            # passed to the simple_deploy CLI.
            self.deployed_project_name = self.sd.deployed_project_name
            self.sd.log_info(f"Deployed project name: {self.deployed_project_name}")
            return

        self._validate_cli()

        self.deployed_project_name = self._get_platformsh_project_name()
        self.sd.log_info(f"Deployed project name: {self.deployed_project_name}")

        self.org_name = self._get_org_name()
        self.sd.log_info(f"\nOrg name: {self.org_name}")

    def _add_platformsh_settings(self):
        """Add platformsh-specific settings.

        The only project-specific setting is ALLOWED_HOSTS. That makes modifying
        settings *much* easier than for other platforms. Just check if the settings are
        present, and if not, dump them in.

        DEV: Modify this to make a more specific ALLOWED_HOSTS entry instead of "*".
        """
        self.sd.write_output(
            "\n  Checking if Platform.sh-specific settings present in settings.py..."
        )

        # PLATFORM_APPLICATION_NAME is an env var that's reliably set in the Platform.sh
        # environment.
        # See: https://docs.platform.sh/development/variables/use-variables.html#use-provided-variables
        settings_string = self.sd.settings_path.read_text()
        if 'if os.environ.get("PLATFORM_APPLICATION_NAME"):' in settings_string:
            self.sd.write_output(
                "\n    Found platform.sh settings block in settings.py."
            )
            return

        # Add platformsh settings block.
        self.sd.write_output(
            "    No platform.sh settings found in settings.py; adding settings..."
        )

        safe_settings_string = mark_safe(settings_string)
        context = {"current_settings": safe_settings_string}
        sd_utils.write_file_from_template(self.sd.settings_path, "settings.py", context)

        msg = f"    Modified settings.py file: {self.sd.settings_path}"
        self.sd.write_output(msg)

    def _generate_platform_app_yaml(self):
        """Create .platform.app.yaml file, if not present."""

        path = self.sd.project_root / ".platform.app.yaml"
        self.sd.write_output(f"\n  Looking for {path.as_posix()}...")

        if path.exists():
            self.sd.write_output("    Found existing .platform.app.yaml file.")
        else:
            # Generate file from template.
            self.sd.write_output(
                "    No .platform.app.yaml file found. Generating file..."
            )

            context = {
                "project_name": self.sd.local_project_name,
                "deployed_project_name": self.deployed_project_name,
            }

            if self.sd.pkg_manager == "poetry":
                template_path = "poetry.platform.app.yaml"
            elif self.sd.pkg_manager == "pipenv":
                template_path = "pipenv.platform.app.yaml"
            else:
                template_path = "platform.app.yaml"
            sd_utils.write_file_from_template(path, template_path, context)

            msg = f"\n    Generated {path.as_posix()}"
            self.sd.write_output(msg)
            return path

    def _add_requirements(self):
        """Add requirements for Platform.sh."""
        requirements = ["platformshconfig", "gunicorn", "psycopg2"]
        self.sd.add_packages(requirements)

    def _make_platform_dir(self):
        """Add a .platform directory, if it doesn't already exist."""

        self.platform_dir_path = self.sd.project_root / ".platform"
        self.sd.write_output(f"\n  Looking for {self.platform_dir_path.as_posix()}...")

        if self.platform_dir_path.exists():
            self.sd.write_output(f"    Found {self.platform_dir_path.as_posix()}")
        else:
            self.platform_dir_path.mkdir()
            self.sd.write_output(f"    Generated {self.platform_dir_path.as_posix()}")

    def _generate_services_yaml(self):
        """Generate the .platform/services.yaml file, if not present."""

        path = self.platform_dir_path / "services.yaml"
        self.sd.write_output(f"\n  Looking for {path.as_posix()}...")

        if path.exists():
            self.sd.write_output("    Found existing services.yaml file.")
        else:
            self.sd.write_output("    No services.yaml file found. Generating file...")
            sd_utils.write_file_from_template(path, "services.yaml")

            msg = f"\n    Generated {path.as_posix()}"
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
        self.sd.write_output("  Pushing to Platform.sh...")

        # Pause to make sure project that was just created can be used.
        self.sd.write_output("    Pausing 10s to make sure project is ready to use...")
        time.sleep(10)

        # Use run_slow_command(), to stream output as it runs.
        cmd = "platform push --yes"
        self.sd.run_slow_command(cmd)

        # Open project.
        self.sd.write_output("  Opening deployed app in a new browser tab...")
        cmd = "platform url --yes"
        output = self.sd.run_quick_command(cmd)
        self.sd.write_output(output)

        # Get url of deployed project.
        #   This can be done with an re, but there's one line of output with
        #   a url, so finding that line is simpler.
        # DEV: Move this to a utility, and write a test against standard Platform.sh
        # output.
        self.deployed_url = ""
        for line in output.stdout.decode().split("\n"):
            if "https" in line:
                self.deployed_url = line.strip()

    def _show_success_message(self):
        """After a successful run, show a message about what to do next."""

        # DEV:
        # - Mention that this script should not need to be run again unless creating
        #   a new deployment.
        # - Describe ongoing approach of commit, push, migrate. Lots to consider
        #   when doing this on production app with users, make sure you learn.

        if self.sd.automate_all:
            msg = self.messages.success_msg_automate_all(self.deployed_url)
            self.sd.write_output(msg)
        else:
            msg = self.messages.success_msg(self.sd.log_output)
            self.sd.write_output(msg)

    # --- Other helper methods ---

    def _prep_automate_all(self):
        """Intial work for automating entire process.

        Returns:
            None: If creation of new project was successful.

        Raises:
            SimpleDeployCommandError: If create command fails.

        Note: create command outputs project id to stdout if known, all other
          output goes to stderr.
        """

        self.sd.write_output("  Running `platform create`...")
        self.sd.write_output("    (Please be patient, this can take a few minutes.")
        cmd = f"platform create --title { self.deployed_project_name } --org {self.org_name} --region {self.sd.region} --yes"

        try:
            # Note: if user can't create a project the returncode will be 6, not 1.
            #   This may affect whether a CompletedProcess is returned, or an Exception
            # is raised.
            # Also, create command outputs project id to stdout if known, all other
            # output goes to stderr.
            self.sd.run_slow_command(cmd)
        except subprocess.CalledProcessError as e:
            error_msg = self.messages.unknown_create_error(e)
            raise SimpleDeployCommandError(self.sd, error_msg)

    # --- Helper methods for methods called from simple_deploy.py ---

    def _validate_cli(self):
        """Make sure the Platform.sh CLI is installed, and user is authenticated."""
        cmd = "platform --version"

        # This generates a FileNotFoundError on Ubuntu if the CLI is not installed.
        try:
            output_obj = self.sd.run_quick_command(cmd)
        except FileNotFoundError:
            raise SimpleDeployCommandError(self.sd, self.messages.cli_not_installed)

        self.sd.log_info(output_obj)

        # Check that the user is authenticated.
        cmd = "platform auth:info --no-interaction"
        output_obj = self.sd.run_quick_command(cmd)

        if "Authentication is required." in output_obj.stderr.decode():
            raise SimpleDeployCommandError(self.sd, self.messages.cli_logged_out)

    def _get_platformsh_project_name(self):
        """Get the deployed project name.

        If using automate_all, we'll set this. Otherwise, we're looking for the name
        that was given in the `platform create` command.
        - Try to get this from `project:info`.
        - If can't get project name:
          - Exit with warning, and inform user of --deployed-project-name
            flag to override this error.

        Retuns:
            str: The deployed project name.
        Raises:
            SimpleDeployCommandError: If deployed project name can't be found.
        """
        # If we're creating the project, we'll just use the startproject name.
        if self.sd.automate_all:
            return self.sd.local_project_name

        # Use the provided name if --deployed-project-name specified.
        if self.sd.deployed_project_name:
            return self.sd.deployed_project_name

        # Use --yes flag to avoid interactive prompt hanging in background
        #   if the user is not currently logged in to the CLI.
        cmd = "platform project:info --yes --format csv"
        output_obj = self.sd.run_quick_command(cmd)
        output_str = output_obj.stdout.decode()

        # Log cmd, but don't log the output of `project:info`. It contains identifying
        # information about the user and project, including client_ssh_key.
        self.sd.log_info(cmd)

        # If there's no stdout, the user is probably logged out, hasn't called
        #   create, or doesn't have the CLI installed.
        # Also, I've seen both ProjectNotFoundException and RootNotFoundException
        #   raised when no project has been created.
        if not output_str:
            output_str = output_obj.stderr.decode()
            if "LoginRequiredException" in output_str:
                raise SimpleDeployCommandError(self.sd, self.messages.login_required)
            elif "ProjectNotFoundException" in output_str:
                raise SimpleDeployCommandError(self.sd, self.messages.no_project_name)
            elif "RootNotFoundException" in output_str:
                raise SimpleDeployCommandError(self.sd, self.messages.no_project_name)
            else:
                error_msg = self.messages.unknown_error
                error_msg += self.messages.cli_not_installed
                raise SimpleDeployCommandError(self.sd, error_msg)

        # Pull deployed project name from output.
        lines = output_str.splitlines()
        title_line = [line for line in lines if "title," in line][0]
        # Assume first project is one to use.
        project_name = title_line.split(",")[1].strip()
        project_name = plsh_utils.get_project_name(output_str)
        if project_name:
            return project_name

        # Couldn't find a project name. Warn user, and tell them about override flag.
        raise SimpleDeployCommandError(self.sd, self.messages.no_project_name)

    def _get_org_name(self):
        """Get the organization name associated with the user's Platform.sh account.

        This is needed for creating a project using automate_all.
        Confirm that it's okay to use this org.

        Returns:
            str: org name
            None: if not using automate-all
        Raises:
            SimpleDeployCommandError:
            - if org name found, but not confirmed.
            - if org name not found
        """
        if not self.sd.automate_all:
            return

        cmd = "platform organization:list --yes --format csv"
        output_obj = self.sd.run_quick_command(cmd)
        output_str = output_obj.stdout.decode()
        self.sd.log_info(output_str)

        if not output_str:
            output_str = output_obj.stderr.decode()
            if "LoginRequiredException" in output_str:
                raise SimpleDeployCommandError(self.sd, self.messages.login_required)
            else:
                error_msg = self.messages.unknown_error
                error_msg += self.messages.cli_not_installed
                raise SimpleDeployCommandError(self.sd, error_msg)

        org_name = plsh_utils.get_org_name(output_str)
        if not org_name:
            raise SimpleDeployCommandError(self.sd, self.messages.org_not_found)

        if self._confirm_use_org_name(org_name):
            return org_name

    def _confirm_use_org_name(self, org_name):
        """Confirm that it's okay to use the org name that was found.

        Returns:
            True: if confirmed
            SimpleDeployCommandError: if not confirmed
        """

        self.stdout.write(self.messages.confirm_use_org_name(org_name))
        confirmed = self.sd.get_confirmation(skip_logging=True)

        if confirmed:
            self.stdout.write("  Okay, continuing with deployment.")
            return True
        else:
            # Exit, with a message that configuration is still an option.
            msg = self.messages.cancel_plsh
            msg += self.messages.may_configure
            raise SimpleDeployCommandError(self.sd, msg)
