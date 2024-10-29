"""Manage deployement to a variety of platforms.

Configuration-only mode: 
    $ python manage.py simple_deploy --platform <platform-name>
    Configures project for deployment to the specified platform.

Automated mode:
    $ python manage.py simple_deploy --platform <platform-name> --automate-all
    Configures project for deployment, *and* issues platform's CLI commands to create
    any resources needed for deployment. Also commits changes, and pushes project.

Overview:
    This is the command that's called to manage the configuration. In the automated
    mode, it also makes the actual deployment. The entire process is coordinated in 
    handle():
    - Parse the CLI options that were passed.
    - Start logging, unless suppressed.
    - Validate the set of arguments that were passed.
    - Inspect the user's system.
    - Inspect the project.
    - Add django-simple-deploy to project requirements.
    - Call the platform's `deploy()` method.

See the project documentation for more about this process:
    https://django-simple-deploy.readthedocs.io/en/latest/
"""

import sys, os, platform, re, subprocess, logging, shlex
from datetime import datetime
from pathlib import Path
from importlib import import_module

from django.core.management.base import BaseCommand
from django.conf import settings

import toml

from . import sd_messages
from .utils import sd_utils
from .utils import plugin_utils
from .utils.sd_config import SDConfig
from . import cli

from simple_deploy.plugins import pm


class Command(BaseCommand):
    """Configure a project for deployment to a specific platform.

    If using --automate-all, carry out the actual deployment as well.
    """

    # Show a summary of simple_deploy in the help text.
    help = "Configures your project for deployment to the specified platform."

    def __init__(self):
        """Customize help output, assign attributes."""

        # Keep default BaseCommand args out of help text.
        self.suppressed_base_arguments.update(
            [
                "--version",
                "-v",
                "--settings",
                "--pythonpath",
                "--traceback",
                "--no-color",
                "--force-color",
            ]
        )
        # Ensure that --skip-checks is not included in help output.
        self.requires_system_checks = []

        super().__init__()

    def create_parser(self, prog_name, subcommand, **kwargs):
        """Customize the ArgumentParser object that will be created."""
        epilog = "For more help, see the full documentation at: "
        epilog += "https://django-simple-deploy.readthedocs.io"
        parser = super().create_parser(
            prog_name,
            subcommand,
            usage=cli.get_usage(),
            epilog=epilog,
            add_help=False,
            **kwargs,
        )

        return parser

    def add_arguments(self, parser):
        """Define CLI options."""
        sd_cli = cli.SimpleDeployCLI(parser)

    def handle(self, *args, **options):
        """Manage the overall configuration process.

        Parse options, start logging, validate the simple_deploy command used, inspect
        the user's system, inspect the project.
        Verify that the user should be able to deploy to this platform.
        Add django-simple-deploy to project requirements.
        Call the platform-specific deploy() method.
        """

        # Create a config object here. This is what's shared with
        # platform-specific plugins.
        self.sd_config = SDConfig(self.stdout)
        plugin_utils.init(self.sd_config)

        plugin_utils.write_output(
            "Configuring project for deployment...", skip_logging=True
        )

        # CLI options need to be parsed before logging starts, in case --no-logging
        # has been passed.
        self._parse_cli_options(options)

        if self.sd_config.log_output:
            self._start_logging()
            self._log_cli_args(options)

        self._validate_command()
        self._inspect_system()
        self._inspect_project()
        self._add_simple_deploy_req()

        # Get the platform-specific deployer module.
        platform_module = import_module(
            f".{self.platform}.deploy", package="simple_deploy.management.commands"
        )
        pm.register(platform_module, self.platform)
        self._check_required_hooks(pm)

        self._confirm_automate_all(pm)
        # sd_config = self._get_sd_config()
        self.sd_config.validate()
        pm.hook.simple_deploy_deploy(sd_config=self.sd_config)

    def _parse_cli_options(self, options):
        """Parse CLI options from simple_deploy command."""

        # Platform-agnostic arguments.
        self.sd_config.automate_all = options["automate_all"]
        self.platform = options["platform"]
        self.sd_config.log_output = not (options["no_logging"])
        self.ignore_unclean_git = options["ignore_unclean_git"]

        # Platform.sh arguments.
        self.sd_config.deployed_project_name = options["deployed_project_name"]
        self.sd_config.region = options["region"]

        # Developer arguments.
        self.sd_config.unit_testing = options["unit_testing"]
        self.sd_config.e2e_testing = options["e2e_testing"]

    def _start_logging(self):
        """Set up for logging.

        Create a log directory if needed; create a new log file for every run of
        simple_deploy. Since simple_deploy should be called once, it's helpful to have
        separate files for each run. It should only be run more than once when users
        are fixing errors that are called out by simple_deploy, or if a remote resource
        hangs.

        Log path is added to .gitignore when the project is inspected.
        See _inspect_project().

        Returns:
            None
        """
        created_log_dir = self._create_log_dir()

        # Instantiate a logger. Append a timestamp so each new run generates a unique
        # log filename.
        timestamp = datetime.now().strftime("%Y-%m-%d-%H%M%S")
        log_filename = f"simple_deploy_{timestamp}.log"
        verbose_log_path = self.log_dir_path / log_filename
        verbose_logger = logging.basicConfig(
            level=logging.INFO,
            filename=verbose_log_path,
            format="%(asctime)s %(levelname)s: %(message)s",
        )

        plugin_utils.write_output(
            "Logging run of `manage.py simple_deploy`..."
        )
        plugin_utils.write_output(f"Created {verbose_log_path}.")

    def _log_cli_args(self, options):
        """Log the args used for this call."""
        plugin_utils.log_info(f"\nCLI args:")
        for option, value in options.items():
            plugin_utils.log_info(f"  {option}: {value}")

    def _create_log_dir(self):
        """Create a directory to hold log files, if not already present.

        Returns:
            bool: True if created directory, False if already one present.
        """
        self.log_dir_path = settings.BASE_DIR / "simple_deploy_logs"
        if not self.log_dir_path.exists():
            self.log_dir_path.mkdir()
            return True
        else:
            return False

    def _validate_command(self):
        """Verify simple_deploy has been called with a valid set of arguments.

        Returns:
            None

        Raises:
            SimpleDeployCommandError: If requested platform is supported.
        """
        if not self.platform:
            raise plugin_utils.SimpleDeployCommandError(
                sd_messages.requires_platform_flag
            )
        elif self.platform in ["fly_io", "platform_sh", "heroku"]:
            plugin_utils.write_output(
                f"\nDeployment target: {self.platform}"
            )
        else:
            error_msg = sd_messages.invalid_platform_msg(self.platform)
            raise plugin_utils.SimpleDeployCommandError(error_msg)

    def _inspect_system(self):
        """Inspect the user's local system for relevant information.

        Uses self.on_windows and self.on_macos because those are clean checks to run.
        May want to refactor to self.user_system at some point. Don't ever use
        self.platform, because "platform" refers to the host we're deploying to.

        Linux is not mentioned because so far, if it works on macOS it works on Linux.
        """
        self.sd_config.use_shell = False
        self.sd_config.on_windows, self.sd_config.on_macos = False, False
        if platform.system() == "Windows":
            self.sd_config.on_windows = True
            self.sd_config.use_shell = True
            plugin_utils.log_info("Local platform identified: Windows")
        elif platform.system() == "Darwin":
            self.sd_config.on_macos = True
            plugin_utils.log_info("Local platform identified: macOS")

    def _inspect_project(self):
        """Inspect the local project.

        Find out everything we need to know about the project before making any remote
        calls.
            Determine project name.
            Find paths: .git/, settings, project root.
            Determine if it's a nested project or not.
            Get the dependency management approach: requirements.txt, Pipenv, Poetry
            Get current requirements.

        Anything that might cause us to exit before making the first remote call should
        be inspected here.

        Sets:
            self.local_project_name, self.project_root, self.settings_path,
            self.pkg_manager, self.requirements

        Returns:
            None
        """
        self.sd_config.local_project_name = settings.ROOT_URLCONF.replace(".urls", "")
        plugin_utils.log_info(
            f"Local project name: {self.sd_config.local_project_name}"
        )

        self.sd_config.project_root = settings.BASE_DIR
        plugin_utils.log_info(
            f"Project root: {self.sd_config.project_root}"
        )

        # Find .git location, and make sure there's a clean status.
        self._find_git_dir()
        self._check_git_status()

        # Now that we know where .git is, we can ignore simple_deploy logs.
        if self.sd_config.log_output:
            self._ignore_sd_logs()

        self.sd_config.settings_path = (
            self.sd_config.project_root
            / self.sd_config.local_project_name
            / "settings.py"
        )

        # Find out which package manager is being used: req_txt, poetry, or pipenv
        self.sd_config.pkg_manager = self._get_dep_man_approach()
        msg = f"Dependency management system: {self.sd_config.pkg_manager}"
        plugin_utils.write_output(msg)

        self.sd_config.requirements = self._get_current_requirements()

    def _find_git_dir(self):
        """Find .git/ location.

        Should be in BASE_DIR or BASE_DIR.parent. If it's in BASE_DIR.parent, this is a
        project with a nested directory structure. A nested project has the structure
        set up by:
           `django-admin startproject project_name`
        A non-nested project has manage.py at the root level, started by:
           `django-admin startproject .`
        This matters for knowing where manage.py is, and knowing where the .git/ dir is
        likely to be.

        Sets:
            self.sd_config.git_path, self.sd_config.nested_project

        Returns:
            None

        Raises:
            SimpleDeployCommandError: If .git/ dir not found.
        """
        if (self.sd_config.project_root / ".git").exists():
            self.sd_config.git_path = self.sd_config.project_root
            plugin_utils.write_output(
                f"Found .git dir at {self.sd_config.git_path}."
            )
            self.sd_config.nested_project = False
        elif (self.project_root.parent / ".git").exists():
            self.sd_config.git_path = self.sd_config.project_root.parent
            plugin_utils.write_output(
                f"Found .git dir at {self.sd_config.git_path}."
            )
            self.sd_config.nested_project = True
        else:
            error_msg = "Could not find a .git/ directory."
            error_msg += f"\n  Looked in {self.sd_config.project_root} and in {self.sd_config.project_root.parent}."
            raise plugin_utils.SimpleDeployCommandError(error_msg)

    def _check_git_status(self):
        """Make sure all non-simple_deploy changes have already been committed.

        All configuration-specific work should be contained in a single commit. This
        allows users to easily revert back to the version of the project that worked
        locally, if the overall deployment effort fails, or if they don't like what
        simple_deploy does for any reason.

        Don't just look for a clean git status. Some uncommitted changes related to
        simple_deploy's work is acceptable, for example if they are doing a couple
        runs to get things right.

        Users can override this check with the --ignore-unclean-git flag.

        Returns:
            None: If status is such that simple_deploy can continue.

        Raises:
            SimpleDeployCommandError: If any reason found not to continue.
        """
        if self.ignore_unclean_git:
            msg = "Ignoring git status."
            plugin_utils.write_output(msg)
            return

        cmd = "git status --porcelain"
        output_obj = plugin_utils.run_quick_command(cmd)
        status_output = output_obj.stdout.decode()
        plugin_utils.log_info(f"{status_output}")

        cmd = "git diff --unified=0"
        output_obj = plugin_utils.run_quick_command(cmd)
        diff_output = output_obj.stdout.decode()
        plugin_utils.log_info(f"{diff_output}\n")

        proceed = sd_utils.check_status_output(status_output, diff_output)

        if proceed:
            msg = "No uncommitted changes, other than simple_deploy work."
            plugin_utils.write_output(msg)
        else:
            self._raise_unclean_error()

    def _raise_unclean_error(self):
        """Raise unclean git status error."""
        error_msg = sd_messages.unclean_git_status
        if self.sd_config.automate_all:
            error_msg += sd_messages.unclean_git_automate_all

        raise plugin_utils.SimpleDeployCommandError(error_msg)

    def _ignore_sd_logs(self):
        """Add log dir to .gitignore.

        Adds a .gitignore file if one is not found.
        """
        ignore_msg = "simple_deploy_logs/\n"

        gitignore_path = self.sd_config.git_path / ".gitignore"
        if not gitignore_path.exists():
            # Make the .gitignore file, and add log directory.
            gitignore_path.write_text(ignore_msg, encoding="utf-8")
            plugin_utils.write_output(
                "No .gitignore file found; created .gitignore."
            )
            plugin_utils.write_output(
                "Added simple_deploy_logs/ to .gitignore."
            )
        else:
            # Append log directory to .gitignore if it's not already there.
            contents = gitignore_path.read_text()
            if "simple_deploy_logs/" not in contents:
                contents += f"\n{ignore_msg}"
                gitignore_path.write_text(contents)
                plugin_utils.write_output(
                    "Added simple_deploy_logs/ to .gitignore"
                )

    def _get_dep_man_approach(self):
        """Identify which dependency management approach the project uses.

        Looks for most specific tests first: Pipenv, Poetry, then requirements.txt. For
        example, if a project uses Poetry and has a requirements.txt file, we'll
        prioritize Poetry.

        Sets:
            self.pkg_manager

        Returns:
            str: "req_txt" | "poetry" | "pipenv"

        Raises:
            SimpleDeployCommandError: If a pkg manager can't be identified.
        """
        if (self.sd_config.git_path / "Pipfile").exists():
            return "pipenv"
        elif self._check_using_poetry():
            return "poetry"
        elif (self.sd_config.git_path / "requirements.txt").exists():
            return "req_txt"

        # Exit if we haven't found any requirements.
        error_msg = (
            f"Couldn't find any specified requirements in {self.sd_config.git_path}."
        )
        raise plugin_utils.SimpleDeployCommandError(error_msg)

    def _check_using_poetry(self):
        """Check if the project appears to be using poetry.

        Check for a pyproject.toml file with a [tool.poetry] section.

        Returns:
            bool: True if found, False if not found.
        """
        path = self.sd_config.git_path / "pyproject.toml"
        if not path.exists():
            return False

        pptoml_data = toml.load(path)
        return "poetry" in pptoml_data.get("tool", {})

    def _get_current_requirements(self):
        """Get current project requirements.

        We need to know which requirements are already specified, so we can add any that
        are needed on the remote platform. We don't need to deal with version numbers
        for most packages.

        Sets:
            self.req_txt_path

        Returns:
            List[str]: List of strings, each representing a requirement.
        """
        msg = "Checking current project requirements..."
        plugin_utils.write_output(msg)

        if self.sd_config.pkg_manager == "req_txt":
            self.sd_config.req_txt_path = self.sd_config.git_path / "requirements.txt"
            requirements = sd_utils.parse_req_txt(self.sd_config.req_txt_path)
        elif self.sd_config.pkg_manager == "pipenv":
            self.sd_config.pipfile_path = self.sd_config.git_path / "Pipfile"
            requirements = sd_utils.parse_pipfile(self.sd_config.pipfile_path)
        elif self.sd_config.pkg_manager == "poetry":
            self.sd_config.pyprojecttoml_path = (
                self.sd_config.git_path / "pyproject.toml"
            )
            requirements = sd_utils.parse_pyproject_toml(
                self.sd_config.pyprojecttoml_path
            )

        # Report findings.
        msg = "  Found existing dependencies:"
        plugin_utils.write_output(msg)
        for requirement in requirements:
            msg = f"    {requirement}"
            plugin_utils.write_output(msg)

        return requirements

    def _add_simple_deploy_req(self):
        """Add django-simple-deploy to the project's requirements.

        Since simple_deploy is in INCLUDED_APPS, it needs to be in the project's
        requirements. If it's missing, platforms will reject the push.
        """
        msg = "\nLooking for django-simple-deploy in requirements..."
        plugin_utils.write_output(msg)
        plugin_utils.add_package("django-simple-deploy")

    def _check_required_hooks(self, pm):
        """Check that all required hooks are implemeted by plugin.

        Returns:
            None
        Raises:
            SimpleDeployCommandError: If hook not found.
        """
        plugin = pm.list_name_plugin()[0][1]

        callers = [caller.name for caller in pm.get_hookcallers(plugin)]
        required_hooks = [
            "simple_deploy_automate_all_supported",
            "simple_deploy_deploy",
        ]
        for hook in required_hooks:
            if hook not in callers:
                msg = f"\nPlugin missing required hook implementation: {hook}()"
                raise plugin_utils.SimpleDeployCommandError(msg)

        # If plugin supports automate_all, make sure a confirmation message is provided.
        if not pm.hook.simple_deploy_automate_all_supported()[0]:
            return

        hook = "simple_deploy_get_automate_all_msg"
        if hook not in callers:
            msg = f"\nPlugin missing required hook implementation: {hook}()"
            raise plugin_utils.SimpleDeployCommandError(msg)

    def _confirm_automate_all(self, pm):
        """Confirm the user understands what --automate-all does.

        Also confirm that the selected platform/ plugin manager supports fully
        automated deployments.

        If confirmation not granted, exit with a message, but no error.
        """
        # Placing this check here keeps the handle() method cleaner.
        if not self.sd_config.automate_all:
            return

        # Make sure this platform supports automate-all.
        supported = pm.hook.simple_deploy_automate_all_supported()[0]
        if not supported:
            msg = "\nThis platform does not support automated deployments."
            msg += "\nYou may want to try again without the --automate-all flag."
            raise plugin_utils.SimpleDeployCommandError(msg)

        # Confirm the user wants to automate all steps.
        msg = pm.hook.simple_deploy_get_automate_all_msg()[0]

        plugin_utils.write_output(msg)
        confirmed = plugin_utils.get_confirmation(self.sd_config)

        if confirmed:
            plugin_utils.write_output("Automating all steps...")
        else:
            # Quit with a message, but don't raise an error.
            plugin_utils.write_output(sd_messages.cancel_automate_all)
            sys.exit()
