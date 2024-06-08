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

from . import deploy_messages
from . import utils
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

        # Make resources available to plugins.
        self.utils = utils
        self.messages = deploy_messages

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
        self.write_output("Configuring project for deployment...", skip_logging=True)

        # CLI options need to be parsed before logging starts, in case --no-logging
        # has been passed.
        self._parse_cli_options(options)

        if self.log_output:
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
        pm.hook.simple_deploy_deploy(sd=self)

    # --- Methods used here, and also by platform-specific modules ---

    def write_output(self, output, write_to_console=True, skip_logging=False):
        """Write output to the appropriate places.

        Typically, this is used for writing output to the console as the configuration
        and deployment work is carried out.  Output may be a string, or an instance of
        subprocess.CompletedProcess.

        Output that's passed to this method typically needs to be logged as well, unless
        skip_logging has been passed. This is useful, for example, when writing
        sensitive information to the console.

        Returns:
            None
        """
        output_str = self.utils.get_string_from_output(output)

        if write_to_console:
            self.stdout.write(output_str)

        if not skip_logging:
            self.log_info(output_str)

    def log_info(self, output):
        """Log output, which may be a string or CompletedProcess instance."""
        if self.log_output:
            output_str = self.utils.get_string_from_output(output)
            self.utils.log_output_string(output_str)

    def run_quick_command(self, cmd, check=False, skip_logging=False):
        """Run a command that should finish quickly.

        Commands that should finish quickly can be run more simply than commands that
        will take a long time. For quick commands, we can capture output and then deal
        with it however we like, and the user won't notice that we first captured
        the output.

        The `check` parameter is included because some callers will need to handle
        exceptions. For example, see prep_automate_all() in deploy_platformsh.py. Most
        callers will only check stderr, or maybe the returncode; they won't need to
        involve exception handling.

        Returns:
            CompletedProcess

        Raises:
            CalledProcessError: If check=True is passed, will raise CPError instead of
            returning a CompletedProcess instance with an error code set.
        """
        if not skip_logging:
            self.log_info(f"\n{cmd}")

        if self.on_windows:
            output = subprocess.run(cmd, shell=True, capture_output=True)
        else:
            cmd_parts = shlex.split(cmd)
            output = subprocess.run(cmd_parts, capture_output=True, check=check)

        return output

    def run_slow_command(self, cmd, skip_logging=False):
        """Run a command that may take some time.

        For commands that may take a while, we need to stream output to the user, rather
        than just capturing it. Otherwise, the command will appear to hang.
        """

        # DEV: This only captures stderr right now.
        # The first call I used this for was `git push heroku`. That call writes to
        # stderr; I believe streaming to stdout and stderr requires multithreading. The
        # current approach seems to be working for all calls that use it.
        #
        # Adding a parameter stdout=subprocess.PIPE and adding a separate identical loop
        # over p.stdout misses stderr. Maybe combine the loops with zip()? SO posts on
        # this topic date back to Python2/3 days.
        if not skip_logging:
            self.log_info(f"\n{cmd}")

        cmd_parts = cmd.split()
        with subprocess.Popen(
            cmd_parts,
            stderr=subprocess.PIPE,
            bufsize=1,
            universal_newlines=True,
            shell=self.use_shell,
        ) as p:
            for line in p.stderr:
                self.write_output(line, skip_logging=skip_logging)

        if p.returncode != 0:
            raise subprocess.CalledProcessError(p.returncode, p.args)

    def get_confirmation(
        self, msg="Are you sure you want to do this?", skip_logging=False
    ):
        """Get confirmation for an action.

        Assumes an appropriate message has already been displayed about what is to be
        done. Shows a yes|no prompt. You can pass a different message for the prompt; it
        should be phrased to elicit a yes/no response.

        Returns:
            bool: True if confirmation granted, False if not granted.
        """
        prompt = f"\n{msg} (yes|no) "
        confirmed = ""

        # If doing e2e testing, always return True.
        if self.e2e_testing:
            self.write_output(prompt, skip_logging=skip_logging)
            msg = "  Confirmed for e2e testing..."
            self.write_output(msg, skip_logging=skip_logging)
            return True

        if self.unit_testing:
            self.write_output(prompt, skip_logging=skip_logging)
            msg = "  Confirmed for unit testing..."
            self.write_output(msg, skip_logging=skip_logging)
            return True

        while True:
            self.write_output(prompt, skip_logging=skip_logging)
            confirmed = input()

            # Log user's response before processing it.
            self.write_output(
                confirmed, skip_logging=skip_logging, write_to_console=False
            )

            if confirmed.lower() in ("y", "yes"):
                return True
            elif confirmed.lower() in ("n", "no"):
                return False
            else:
                self.write_output(
                    "  Please answer yes or no.", skip_logging=skip_logging
                )

    def check_settings(self, platform_name, start_line, msg_found, msg_cant_overwrite):
        """Check if a platform-specific settings block already exists.

        If so, ask if we can overwrite that block. This is much simpler than trying to
        keep track of individual settings.

        Returns:
            None

        Raises:
            SimpleDeployCommandError: If we can't overwrite existing platform-specific
            settings block.
        """
        settings_text = self.settings_path.read_text()

        re_platform_settings = f"(.*)({start_line})(.*)"
        m = re.match(re_platform_settings, settings_text, re.DOTALL)

        if not m:
            self.log_info(f"No {platform_name}-specific settings block found.")
            return

        # A platform-specific settings block exists. Get permission to overwrite it.
        if not self.get_confirmation(msg_found):
            raise self.utils.SimpleDeployCommandError(self, msg_cant_overwrite)

        # Platform-specific settings exist, but we can remove them and start fresh.
        self.settings_path.write_text(m.group(1))

        msg = f"  Removed existing {platform_name}-specific settings block."
        self.write_output(msg)

    def add_packages(self, package_list):
        """Add a set of packages to the project's requirements.

        This is a simple wrapper for add_package(), to make it easier to add multiple
        requirements at once. If you need to specify a version for a particular package,
        use add_package().

        Returns:
            None
        """
        for package in package_list:
            self.add_package(package)

    def add_package(self, package_name, version=""):
        """Add a package to the project's requirements, if not already present.

        Handles calls with version information with pip formatting:
            add_package("psycopg2", version="<2.9")
        The utility methods handle this version information correctly for the dependency
        management system in use.

        Returns:
            None
        """
        self.write_output(f"\nLooking for {package_name}...")

        if package_name in self.requirements:
            self.write_output(f"  Found {package_name} in requirements file.")
            return

        if self.pkg_manager == "pipenv":
            self.utils.add_pipenv_pkg(self.pipfile_path, package_name, version)
        elif self.pkg_manager == "poetry":
            self._check_poetry_deploy_group()
            self.utils.add_poetry_pkg(self.pyprojecttoml_path, package_name, version)
        else:
            self.utils.add_req_txt_pkg(self.req_txt_path, package_name, version)

        self.write_output(f"  Added {package_name} to requirements file.")

    def commit_changes(self):
        """Commit changes that have been made to the project.

        This should only be called when automate_all is being used.
        """
        if not self.automate_all:
            return

        self.write_output("  Committing changes...")

        cmd = "git add ."
        output = self.run_quick_command(cmd)
        self.write_output(output)

        cmd = 'git commit -m "Configured project for deployment."'
        output = self.run_quick_command(cmd)
        self.write_output(output)

    # --- Internal methods; used only in this class ---

    def _parse_cli_options(self, options):
        """Parse CLI options from simple_deploy command."""

        # Platform-agnostic arguments.
        self.automate_all = options["automate_all"]
        self.platform = options["platform"]
        self.log_output = not (options["no_logging"])
        self.ignore_unclean_git = options["ignore_unclean_git"]

        # Platform.sh arguments.
        self.deployed_project_name = options["deployed_project_name"]
        self.region = options["region"]

        # Developer arguments.
        self.unit_testing = options["unit_testing"]
        self.e2e_testing = options["e2e_testing"]

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

        self.write_output("Logging run of `manage.py simple_deploy`...")
        self.write_output(f"Created {verbose_log_path}.")

    def _log_cli_args(self, options):
        """Log the args used for this call."""
        self.log_info(f"\nCLI args:")
        for option, value in options.items():
            self.log_info(f"  {option}: {value}")

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
            raise self.utils.SimpleDeployCommandError(
                self, deploy_messages.requires_platform_flag
            )
        elif self.platform in ["fly_io", "platform_sh", "heroku"]:
            self.write_output(f"\nDeployment target: {self.platform}")
        else:
            error_msg = deploy_messages.invalid_platform_msg(self.platform)
            raise self.utils.SimpleDeployCommandError(self, error_msg)

    def _inspect_system(self):
        """Inspect the user's local system for relevant information.

        Uses self.on_windows and self.on_macos because those are clean checks to run.
        May want to refactor to self.user_system at some point. Don't ever use
        self.platform, because "platform" refers to the host we're deploying to.

        Linux is not mentioned because so far, if it works on macOS it works on Linux.
        """
        self.use_shell = False
        self.on_windows, self.on_macos = False, False
        if platform.system() == "Windows":
            self.on_windows = True
            self.use_shell = True
            self.log_info("Local platform identified: Windows")
        elif platform.system() == "Darwin":
            self.on_macos = True
            self.log_info("Local platform identified: macOS")

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
        self.local_project_name = settings.ROOT_URLCONF.replace(".urls", "")
        self.log_info(f"Local project name: {self.local_project_name}")

        self.project_root = settings.BASE_DIR
        self.log_info(f"Project root: {self.project_root}")

        # Find .git location, and make sure there's a clean status.
        self._find_git_dir()
        self._check_git_status()

        # Now that we know where .git is, we can ignore simple_deploy logs.
        if self.log_output:
            self._ignore_sd_logs()

        self.settings_path = self.project_root / self.local_project_name / "settings.py"

        # Find out which package manager is being used: req_txt, poetry, or pipenv
        self.pkg_manager = self._get_dep_man_approach()
        msg = f"Dependency management system: {self.pkg_manager}"
        self.write_output(msg)

        self.requirements = self._get_current_requirements()

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
            self.git_path, self.nested_project

        Returns:
            None

        Raises:
            SimpleDeployCommandError: If .git/ dir not found.
        """
        if (self.project_root / ".git").exists():
            self.git_path = self.project_root
            self.write_output(f"Found .git dir at {self.git_path}.")
            self.nested_project = False
        elif (self.project_root.parent / ".git").exists():
            self.git_path = self.project_root.parent
            self.write_output(f"Found .git dir at {self.git_path}.")
            self.nested_project = True
        else:
            error_msg = "Could not find a .git/ directory."
            error_msg += (
                f"\n  Looked in {self.project_root} and in {self.project_root.parent}."
            )
            raise self.utils.SimpleDeployCommandError(self, error_msg)

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
            self.write_output(msg)
            return

        cmd = "git status --porcelain"
        output_obj = self.run_quick_command(cmd)
        status_output = output_obj.stdout.decode()
        self.log_info(f"{status_output}")

        cmd = "git diff --unified=0"
        output_obj = self.run_quick_command(cmd)
        diff_output = output_obj.stdout.decode()
        self.log_info(f"{diff_output}\n")

        proceed = self.utils.check_status_output(status_output, diff_output)

        if proceed:
            msg = "No uncommitted changes, other than simple_deploy work."
            self.write_output(msg)
        else:
            self._raise_unclean_error()

    def _raise_unclean_error(self):
        """Raise unclean git status error."""
        error_msg = deploy_messages.unclean_git_status
        if self.automate_all:
            error_msg += deploy_messages.unclean_git_automate_all

        raise self.utils.SimpleDeployCommandError(self, error_msg)

    def _ignore_sd_logs(self):
        """Add log dir to .gitignore.

        Adds a .gitignore file if one is not found.
        """
        ignore_msg = "simple_deploy_logs/\n"

        gitignore_path = self.git_path / ".gitignore"
        if not gitignore_path.exists():
            # Make the .gitignore file, and add log directory.
            gitignore_path.write_text(ignore_msg, encoding="utf-8")
            self.write_output("No .gitignore file found; created .gitignore.")
            self.write_output("Added simple_deploy_logs/ to .gitignore.")
        else:
            # Append log directory to .gitignore if it's not already there.
            contents = gitignore_path.read_text()
            if "simple_deploy_logs/" not in contents:
                contents += f"\n{ignore_msg}"
                gitignore_path.write_text(contents)
                self.write_output("Added simple_deploy_logs/ to .gitignore")

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
        if (self.git_path / "Pipfile").exists():
            return "pipenv"
        elif self._check_using_poetry():
            return "poetry"
        elif (self.git_path / "requirements.txt").exists():
            return "req_txt"

        # Exit if we haven't found any requirements.
        error_msg = f"Couldn't find any specified requirements in {self.git_path}."
        raise self.utils.SimpleDeployCommandError(self, error_msg)

    def _check_using_poetry(self):
        """Check if the project appears to be using poetry.

        Check for a pyproject.toml file with a [tool.poetry] section.

        Returns:
            bool: True if found, False if not found.
        """
        path = self.git_path / "pyproject.toml"
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
        self.write_output(msg)

        if self.pkg_manager == "req_txt":
            self.req_txt_path = self.git_path / "requirements.txt"
            requirements = self.utils.parse_req_txt(self.req_txt_path)
        elif self.pkg_manager == "pipenv":
            self.pipfile_path = self.git_path / "Pipfile"
            requirements = self.utils.parse_pipfile(self.pipfile_path)
        elif self.pkg_manager == "poetry":
            self.pyprojecttoml_path = self.git_path / "pyproject.toml"
            requirements = self.utils.parse_pyproject_toml(self.pyprojecttoml_path)

        # Report findings.
        msg = "  Found existing dependencies:"
        self.write_output(msg)
        for requirement in requirements:
            msg = f"    {requirement}"
            self.write_output(msg)

        return requirements

    def _add_simple_deploy_req(self):
        """Add django-simple-deploy to the project's requirements.

        Since simple_deploy is in INCLUDED_APPS, it needs to be in the project's
        requirements. If it's missing, platforms will reject the push.
        """
        msg = "\nLooking for django-simple-deploy in requirements..."
        self.write_output(msg)
        self.add_package("django-simple-deploy")

    def _check_poetry_deploy_group(self):
        """Make sure a deploy group exists in pyproject.toml."""
        pptoml_data = toml.load(self.pyprojecttoml_path)
        try:
            deploy_group = pptoml_data["tool"]["poetry"]["group"]["deploy"]
        except KeyError:
            self.utils.create_poetry_deploy_group(self.pyprojecttoml_path)
            msg = "    Added optional deploy group to pyproject.toml."
            self.write_output(msg)

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
                raise self.utils.SimpleDeployCommandError(self, msg)

        # If plugin supports automate_all, make sure a confirmation message is provided.
        if not pm.hook.simple_deploy_automate_all_supported()[0]:
            return

        hook = "simple_deploy_get_automate_all_msg"
        if hook not in callers:
            msg = f"\nPlugin missing required hook implementation: {hook}()"
            raise self.utils.SimpleDeployCommandError(self, msg)

    def _confirm_automate_all(self, pm):
        """Confirm the user understands what --automate-all does.

        Also confirm that the selected platform/ plugin manager supports fully
        automated deployments.

        If confirmation not granted, exit with a message, but no error.
        """
        # Placing this check here keeps the handle() method cleaner.
        if not self.automate_all:
            return

        # Make sure this platform supports automate-all.
        supported = pm.hook.simple_deploy_automate_all_supported()[0]
        if not supported:
            msg = "\nThis platform does not support automated deployments."
            msg += "\nYou may want to try again without the --automate-all flag."
            raise self.utils.SimpleDeployCommandError(self, msg)

        # Confirm the user wants to automate all steps.
        msg = pm.hook.simple_deploy_get_automate_all_msg()[0]

        self.write_output(msg)
        confirmed = self.get_confirmation()

        if confirmed:
            self.write_output("Automating all steps...")
        else:
            # Quit with a message, but don't raise an error.
            self.write_output(deploy_messages.cancel_automate_all)
            sys.exit()
