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
    - Get confirmation for an automated run, if appropriate.
    - Call the platform's `validate_platform()` method.
    - In automated mode, call the platform's `prep_automate_all()` method.
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

from . import deploy_messages as d_msgs
from . import utils as sd_utils
from . import cli


class Command(BaseCommand):
    """Configure a project for deployment to a specific platform.

    If using --automate-all, carry out the actual deployment as well.
    """

    # Show a summary of simple_deploy in the help text.
    help = "Configures your project for deployment to the specified platform."

    def __init__(self):
        """Customize help output."""

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
        self.write_output("Configuring project for deployment...", skip_logging=True)

        # CLI options need to be parsed before logging starts, in case --no-logging
        # has been passed.
        self._parse_cli_options(options)

        if self.log_output:
            self._start_logging()
            self.log_info(f"\nCLI args: {options}")

        self._validate_command()
        self._prep_platform()
        self._inspect_system()
        self._inspect_project()

        # Confirm --automate-all before calling platform.validate_platform(), because
        # some platforms will take validation actions based on whether it's a
        # configuration-only run or an automated deployment.
        self._confirm_automate_all()

        self.platform_deployer.validate_platform()

        # First action that could fail, but should happen after logging, is
        #   calling platform-specific prep_automate_all(). This usually creates
        #   an empty project on the target platform. This is one of the steps
        #   most likely to fail, so it should be called before other modifications.
        if self.automate_all:
            self.platform_deployer.prep_automate_all()

        self._add_simple_deploy_req()

        # All platform-agnostic work has been completed. Call platform-specific
        #   deploy() method.
        self.platform_deployer.deploy()

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
        output_str = sd_utils.get_string_from_output(output)

        if write_to_console:
            self.stdout.write(output_str)

        if not skip_logging:
            self.log_info(output_str)

    def log_info(self, output):
        """Log output, which may be a string or CompletedProcess instance."""
        if self.log_output:
            output_str = sd_utils.get_string_from_output(output)
            sd_utils.log_output_string(output_str)

    def execute_subp_run(self, cmd, check=False):
        """Execute subprocess.run() command.
        We're running commands differently on Windows, so this method
          takes a command and runs it appropriately on each system.

        The `check` parameter is included because some callers will need to
          handle exceptions. For an example, see prep_automate_all() in
          deploy_platformsh.py. Most callers will only check whether returncode
          is nonzero, and not need to involve exception handling.

        Returns:
            - CompletedProcess instance
            - if check=True is passed, raises CalledProcessError instead of
              CompletedProcess with an error code.
        """
        if self.on_windows:
            output = subprocess.run(cmd, shell=True, capture_output=True)
        else:
            cmd_parts = shlex.split(cmd)
            output = subprocess.run(cmd_parts, capture_output=True, check=check)

        return output

    def execute_command(self, cmd, skip_logging=False):
        """Execute command, and stream output while logging.
        This method is intended for commands that run long enough that we
        can't use a simple subprocess.run(capture_output=True), which doesn't
        stream any output until the command is finished. That works for logging,
        but makes it seem as if the deployment is hanging. This is an issue
        especially on platforms like Azure that have some steps that take minutes
        to run.
        """

        # DEV: This only captures stderr right now.
        #   This is used for commands that run long enough that we don't
        #   want to use a simple subprocess.run(capture_output=True). Right
        #   now that's the `git push heroku` call. That call writes to
        #   stderr; I'm not sure how to stream both stdout and stderr. It also
        #   affects `platform create` and `platform push`.
        #
        #     This will also be needed for long-running steps on other platforms,
        #   which may or may not write to stderr. Adding a parameter
        #   stdout=subprocess.PIPE and adding a separate identical loop over p.stdout
        #   misses stderr. Maybe combine the loops with zip()? SO posts on this
        #   topic date back to Python2/3 days.
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
        self.integration_testing = options["integration_testing"]

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

        self.log_info("\nLogging run of `manage.py simple_deploy`...")
        if created_log_dir:
            self.write_output(f"Created {self.log_dir_path}.")

    def _create_log_dir(self):
        """Create a directory to hold log files, if not already present.

        Returns:
            bool: True if created directory, False if already one present.
        """
        self.log_dir_path = settings.BASE_DIR / Path("simple_deploy_logs")
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
            raise sd_utils.SimpleDeployCommandError(self, d_msgs.requires_platform_flag)
        elif self.platform in ["fly_io", "platform_sh", "heroku"]:
            self.write_output(f"  Deployment target: {self.platform}")
        else:
            error_msg = d_msgs.invalid_platform_msg(self.platform)
            raise sd_utils.SimpleDeployCommandError(self, error_msg)

    def _prep_platform(self):
        """Prepare platform-specific resources needed in this module.

        Instantiate the PlatformDeployer object.
        Import platform-specific messages.
        Get confirmation regarding preliminary support, if needed.
        """
        deployer_module = import_module(
            f".{self.platform}.deploy", package="simple_deploy.management.commands"
        )
        self.platform_deployer = deployer_module.PlatformDeployer(self)

        self.platform_msgs = import_module(
            f".{self.platform}.deploy_messages",
            package="simple_deploy.management.commands",
        )

        try:
            self.platform_deployer.confirm_preliminary()
        except AttributeError:
            pass

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
            self.log_info("  Local platform identified: Windows")
        elif platform.system() == "Darwin":
            self.on_macos = True
            self.log_info("  Local platform identified: macOS")

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
        self.log_info(f"  Local project name: {self.local_project_name}")

        self.project_root = settings.BASE_DIR
        self.log_info(f"  Project root: {self.project_root}")

        # Find .git location, and make sure there's a clean status.
        self._find_git_dir()
        self._check_git_status()

        # Now that we know where .git is, we can ignore simple_deploy logs.
        if self.log_output:
            self._ignore_sd_logs()

        self.settings_path = self.project_root / self.local_project_name / "settings.py"

        # Find out which package manager is being used: req_txt, poetry, or pipenv
        self.pkg_manager = self._get_dep_man_approach()
        msg = f"  Dependency management system: {self.pkg_manager}"
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
            self.write_output(f"  Found .git dir at {self.git_path}.")
            self.nested_project = False
        elif (self.project_root.parent / ".git").exists():
            self.git_path = self.project_root.parent
            self.write_output(f"  Found .git dir at {self.git_path}.")
            self.nested_project = True
        else:
            error_msg = "Could not find a .git/ directory."
            error_msg += (
                f"\n  Looked in {self.project_root} and in {self.project_root.parent}."
            )
            raise sd_utils.SimpleDeployCommandError(self, error_msg)

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
        output_obj = self.execute_subp_run(cmd)
        status_output = output_obj.stdout.decode()
        self.log_info(f"\n{cmd}:\n{status_output}\n")

        cmd = "git diff --unified=0"
        output_obj = self.execute_subp_run(cmd)
        diff_output = output_obj.stdout.decode()
        self.log_info(f"\n{cmd}:\n{diff_output}\n")

        proceed = sd_utils.check_status_output(status_output, diff_output)

        if proceed:
            msg = "No uncommitted changes, other than simple_deploy work."
            self.write_output(msg)
        else:
            self._raise_unclean_error()

    def _raise_unclean_error(self):
        """Raise unclean git status error."""
        error_msg = d_msgs.unclean_git_status
        if self.automate_all:
            error_msg += d_msgs.unclean_git_automate_all

        raise sd_utils.SimpleDeployCommandError(self, error_msg)

    def _ignore_sd_logs(self):
        """Add log dir to .gitignore.
        Adds a .gitignore file if one is not found.
        """
        ignore_msg = "# Ignore logs from simple_deploy."
        ignore_msg += "\nsimple_deploy_logs/\n"

        # Assume .gitignore is in same directory as .git/ directory.
        # gitignore_path = Path(settings.BASE_DIR) / Path('.gitignore')
        gitignore_path = self.git_path / ".gitignore"
        if not gitignore_path.exists():
            # Make the .gitignore file, and add log directory.
            gitignore_path.write_text(ignore_msg, encoding="utf-8")
            self.write_output("No .gitignore file found; created .gitignore.")
            self.write_output("Added simple_deploy_logs/ to .gitignore.")
        else:
            # Append log directory to .gitignore if it's not already there.
            # In r+ mode, a single read moves file pointer to end of file,
            #   setting up for appending.
            with open(gitignore_path, "r+") as f:
                gitignore_contents = f.read()
                if "simple_deploy_logs/" not in gitignore_contents:
                    f.write(f"\n{ignore_msg}")
                    self.write_output("Added simple_deploy_logs/ to .gitignore")

    # fmt: off
    def _get_dep_man_approach(self):
        """Identify which dependency management approach the project uses.
        req_txt, poetry, or pipenv.

        Sets the self.pkg_manager attribute.
        Looks for most specific tests first: Pipenv, Poetry, then requirements.txt.
          ie if a project uses Poetry and has a requirements.txt file, we'll prioritize
          Poetry.

        Returns
        - String representing dependency management system found:
            req_txt | poetry | pipenv
        - Raises CommandError if no pkg_manager can be identified.
        """
        if (self.git_path / "Pipfile").exists():
            return "pipenv"
        elif self._check_using_poetry():
            return "poetry"
        elif (self.git_path / "requirements.txt").exists():
            return "req_txt"

        # Exit if we haven't found any requirements.
        error_msg = f"Couldn't find any specified requirements in {self.git_path}."
        raise sd_utils.SimpleDeployCommandError(self, error_msg)


    def _check_using_poetry(self):
        """Check if the project appears to be using poetry.

        Check for a poetry.lock file, or a pyproject.toml file with a
          [tool.poetry] section.

        Returns:
        - True if one of these is found.
        - False if one of these is not found.
        """
        path = self.git_path / "poetry.lock"
        if path.exists():
            return True

        path = self.git_path / "pyproject.toml"
        if path.exists():
            if "[tool.poetry]" in path.read_text():
                return True

        # Couldn't find any evidence of using Poetry.
        return False

    def _get_current_requirements(self):
        """Get current project requirements, before adding any new ones.

        Returns:
        - List of requirements, with no version information.
        """
        msg = "  Checking current project requirements..."
        self.write_output(msg)

        if self.pkg_manager == "req_txt":
            requirements = self._get_req_txt_requirements()
        elif self.pkg_manager == "pipenv":
            requirements = self._get_pipfile_requirements()
        elif self.pkg_manager == "poetry":
            requirements = self._get_poetry_requirements()

        # Report findings. 
        msg = "    Found existing dependencies:"
        self.write_output(msg)
        for requirement in requirements:
            msg = f"      {requirement}"
            self.write_output(msg)

        return requirements

    def _get_req_txt_requirements(self):
        """Get a list of requirements from the current requirements.txt file.

        Parses requirements.txt file directly, rather than using a command
          like `pip list`. `pip list` lists all installed packages, but they
          may not be in requirements.txt, depending on when `pip freeze` was
          last run. This is different than other dependency management systems,
          which write to various requirements files whenever a package is installed.

        Returns:
        - List of requirements, with no version information.
        """
        # This path will be used later, so make it an attribute.
        self.req_txt_path = self.git_path / "requirements.txt"
        contents = self.req_txt_path.read_text()
        lines = contents.split("\n")

        # Parse requirements file, without including version information.
        req_re = r'^([a-zA-Z0-9\-]*)'
        requirements = []
        for line in lines:
            m = re.search(req_re, line)
            if m:
                requirements.append(m.group(1))

        return requirements


    def _get_pipfile_requirements(self):
        """Get a list of requirements that are already in the Pipfile.

        Parses Pipfile, because we don't want to trust a lock file, and we need
          to examine packages that may be listed in Pipfile but not currently
          installed.

        Returns:
        - List of requirements, without version information.
        """
        # The path to pipfile is used when writing to pipfile as well.
        self.pipfile_path = f"{self.git_path}/Pipfile"

        with open(self.pipfile_path) as f:
            lines = f.readlines()

        requirements = []
        in_packages = False
        for line in lines:
            # Ignore all lines until we've found the start of packages.
            #   Stop parsing when we hit dev-packages.
            if '[packages]' in line:
                in_packages = True
                continue
            elif '[dev-packages]' in line:
                # Ignore dev packages for now.
                break

            if in_packages:
                pkg_name = line.split('=')[0].rstrip()

                # Ignore blank lines.
                if pkg_name:
                    requirements.append(pkg_name)

        return requirements

    def _get_poetry_requirements(self):
        """Get a list of requirements that Poetry is already tracking.

        Parses pyproject.toml file. It's easier to work with the output of 
          `poetry show`, but that examines poetry.lock. We are interested in
          what's written to pyproject.toml, not what's in the lock file.

        Returns:
        - List of requirements, with no version information.
        """
        # We'll use this again, so make it an attribute.
        self.pyprojecttoml_path = self.git_path / "pyproject.toml"
        parsed_toml = toml.loads(self.pyprojecttoml_path.read_text())

        # For now, just examine main requirements and deploy group requirements.
        main_reqs = parsed_toml['tool']['poetry']['dependencies'].keys()
        requirements = list(main_reqs)
        try:
            deploy_reqs = parsed_toml['tool']['poetry']['group']['deploy']['dependencies'].keys()
        except KeyError:
            # This group doesn't exist yet, which is fine.
            pass
        else:
            requirements += list(deploy_reqs)

        # Remove python as a requirement, as we're only interested in packages.
        requirements.remove("python")

        return requirements



    def _confirm_automate_all(self):
        """If the --automate-all flag has been passed, confirm that the user
        really wants us to take these actions for them.
        """

        # Placing this check here makes handle() much cleaner.
        if not self.automate_all:
            return

        # Confirm the user knows exactly what will be automated.
        self.write_output(self.platform_msgs.confirm_automate_all)
        confirmed = self.get_confirmation()

        if confirmed:
            self.write_output("Automating all steps...")
        else:
            # Quit and have the user run the command again; don't assume not
            #   wanting to automate means they want to configure.
            self.write_output(d_msgs.cancel_automate_all)
            sys.exit()

    def _add_simple_deploy_req(self):
        """Add this project to requirements.txt."""
        # Since the simple_deploy app is in INCLUDED_APPS, it needs to be
        #   required. If it's not, platforms will reject the push.
        # This step isn't needed for Pipenv users, because when they install
        #   django-simple-deploy it's automatically added to Pipfile.
        # if self.pkg_manager != "pipenv":
        #     self.write_output("\n  Looking for django-simple-deploy in requirements...")
        #     self.add_package('django-simple-deploy')

        # Do this for all package managers, until testing better sorted?
        self.write_output("\n  Looking for django-simple-deploy in requirements...")
        self.add_package('django-simple-deploy')

    def _write_pipfile_pkg(self, package_name, version=""):
        """Write package to Pipfile."""

        with open(self.pipfile_path) as f:
            pipfile_text = f.read()

        if not version:
            version = '*'

        # Don't make ugly comments; make space to align comments.
        #   Align at column 30, so take away name length, and version spec space.
        tab_string = ' ' * (30 - len(package_name) - 5 - len(version))

        # Write package name right after [packages].
        #   For simple projects, this shouldn't cause any issues.
        #   If ordering matters, we can address that later.
        new_pkg_string = f'[packages]\n{package_name} = "{version}"{tab_string}# Added by simple_deploy command.'
        pipfile_text = pipfile_text.replace("[packages]", new_pkg_string)

        with open(self.pipfile_path, 'w') as f:
            f.write(pipfile_text)

        self.write_output(f"    Added {package_name} to Pipfile.")


    # --- Methods also used by platform-specific scripts ---

    def add_packages(self, package_list):
        """Adds a set of packages to the project's requirements.
        
        This is a simple wrapper for add_package(), to make it easier to add 
          multiple requirements at once.
        If you need to specify a version for a particular package,
          use add_package().

        Returns:
        - None
        """
        for package in package_list:
            self.add_package(package)


    def add_package(self, package_name, version=""):
        """Add a pacakage to the project's requirements.

        This method is pkg_manager-agnostic. It delegates to a method that's 
          specific to the dependency management system that's in use.

        Handles calls with version information with pip formatting:
        - self.sd.add_package("psycopg2", version="<2.9")
        The delegated methods handle this version information correctly for
          the dependency management system in use.

        Returns:
        - None
        """
        self.write_output(f"\n  Looking for {package_name}...")

        if self.pkg_manager == "pipenv":
            self._add_pipenv_pkg(package_name, version)
        elif self.pkg_manager == "poetry":
            self._add_poetry_pkg(package_name, version)
        else:
            self._add_req_txt_pkg(package_name, version)


    def _add_req_txt_pkg(self, package_name, version):
        """Add a package to requirements.txt, if not already present.

        Returns:
        - None
        """
        # Note: This does not check for specific versions. It gives priority
        #   to any version already specified in requirements.
        if package_name in self.requirements:
            self.write_output(f"    Found {package_name} in requirements file.")
            return

        # Package not in requirements.txt, so add it.
        with open(self.req_txt_path, 'a') as f:
            # Add version information to package name, ie "pscopg2<2.9".
            package_name += version
            # Align comments, so we don't make req_txt file ugly.
            tab_string = ' ' * (30 - len(package_name))
            f.write(f"\n{package_name}{tab_string}# Added by simple_deploy command.")

        self.write_output(f"    Added {package_name} to requirements.txt.")


    def _add_poetry_pkg(self, package_name, version):
        """Add a package when project is using Poetry.

        Adds an entry to pyproject.toml, without modifying the lock file.
        Ensures the optional "deploy" group exists, and creates it if not.
        Returns:
        - None
        """
        self._check_poetry_deploy_group()

        # Check if package already in pyproject.toml.
        if package_name in self.requirements:
            self.write_output(f"    Found {package_name} in requirements file.")
            return

        # Add package to pyproject.toml.
        #   Define new requirement entry, read contents, replace group definition
        #   with group definition plus new requirement line. This has the effect
        #   of adding each new requirement to the beginning of the deploy group.
        # DEV: `version` should just be a default arg, instead of having an if block here.
        if not version:
            version = "*"
        new_req_line = f'{package_name} = "{version}"'

        contents = self.pyprojecttoml_path.read_text()
        new_group_string = f"{self.poetry_group_string}{new_req_line}\n"
        contents = contents.replace(self.poetry_group_string, new_group_string)
        self.pyprojecttoml_path.write_text(contents, encoding='utf-8')

        self.write_output(f"    Added {package_name} to pyproject.toml.")

    def _check_poetry_deploy_group(self):
        """Make sure that an optional deploy group exists in pyproject.toml.

        If the group does not exist, write that group in pyproject.toml.
          Establish the opening lines as an attribute, to make it easier to
          add packages later.

        Returns:
        - None
        """
        self.poetry_group_string = "[tool.poetry.group.deploy]\noptional = true\n"
        self.poetry_group_string += "\n[tool.poetry.group.deploy.dependencies]\n"

        contents = self.pyprojecttoml_path.read_text()

        if self.poetry_group_string in contents:
            # Group already exists, we don't need to do anything.
            return
        
        # Group not found, so create it now.
        contents += f"\n\n{self.poetry_group_string}"
        self.pyprojecttoml_path.write_text(contents, encoding='utf-8')

        msg = '    Added optional "deploy" group to pyproject.toml.'
        self.write_output(msg)


    def _add_pipenv_pkg(self, package_name, version=""):
        """Add a package to Pipfile, if not already present.

        Returns:
        - None
        """
        if package_name in self.requirements:
            self.write_output(f"    Found {package_name} in Pipfile.")
        else:
            self._write_pipfile_pkg(package_name, version)


    def get_confirmation(self, msg="", skip_logging=False):
        """Get confirmation for an action.
        This method assumes an appropriate message has already been displayed
          about what is to be done.
        You can pass a different message for the prompt; it should be phrased
          to elicit a yes/no response. Don't include the yes/no part.
        This method shows a yes|no prompt, and returns True or False.

        DEV: This should probably be moved to utils.
        """
        if not msg:
            prompt = "\nAre you sure you want to do this? (yes|no) "
        else:
            prompt = f"\n{msg} (yes|no) "
        confirmed = ''

        # If doing integration testing, always return True.
        if self.integration_testing:
            self.write_output(prompt, skip_logging=skip_logging)
            msg = "  Confirmed for integration testing..."
            self.write_output(msg, skip_logging=skip_logging)
            return True

        while True:
            self.write_output(prompt, skip_logging=skip_logging)
            confirmed = input()

            # Log user's response before processing it.
            self.write_output(confirmed, skip_logging=skip_logging,
                    write_to_console=False)

            if confirmed.lower() in ('y', 'yes'):
                return True
            elif confirmed.lower() in ('n', 'no'):
                return False
            else:
                self.write_output("  Please answer yes or no.",
                        skip_logging=skip_logging)


    def commit_changes(self):
        """Commit changes that have been made to the project.
        This should only be called when automate_all is being used.
        """
        if not self.automate_all:
            return

        self.write_output("  Committing changes...")

        cmd = 'git add .'
        output = self.execute_subp_run(cmd)
        self.write_output(output)

        cmd = 'git commit -am "Configured project for deployment."'
        output = self.execute_subp_run(cmd)
        self.write_output(output)
