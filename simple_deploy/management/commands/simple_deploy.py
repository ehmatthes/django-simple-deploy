"""Handles all platform-agnostic aspects of the deployment process."""

# This is the command that's called to automate deployment.
# - It starts the process, and then dispatches to platform-specific helpers.
# - Each helper gets a reference to this command object.


import sys, os, platform, re, subprocess, logging, shlex
from datetime import datetime
from pathlib import Path
from importlib import import_module

from django.core.management.base import BaseCommand, CommandError
from django.conf import settings
import toml

from . import deploy_messages as d_msgs
from .utils import write_file_from_template
from . import cli


class Command(BaseCommand):
    """Perform the initial deployment of a simple project.
    Configure as much as possible automatically.
    """

    # Provide a summary of simple_deploy in the help text.
    help = "Configures your project for deployment to the specified platform."

    def __init__(self):
        """Customize help output."""

        # Keep default BaseCommand args out of our help text.
        self.suppressed_base_arguments.update([
            '--version', '-v', '--settings', '--pythonpath', '--traceback', '--no-color',
            '--force-color'
            ])
        # Ensure that --skip-checks is not included in help output.
        self.requires_system_checks = []

        super().__init__()


    def create_parser(self, prog_name, subcommand, **kwargs):
        """Customize the ArgumentParser object that will be created."""
        epilog = "For more help, see the full documentation at: https://django-simple-deploy.readthedocs.io"
        parser = super().create_parser(prog_name, subcommand, usage=cli.get_usage(),
                epilog=epilog, add_help=False, **kwargs)

        return parser


    def add_arguments(self, parser):
        """Define CLI options."""
        sd_cli = cli.SimpleDeployCLI(parser)


    def handle(self, *args, **options):
        """Parse options, and dispatch to platform-specific helpers."""
        self.stdout.write("Configuring project for deployment...")

        # Parse CLI options, and validate the set of arguments we've been given.
        #   _validate_command() instantiates a PlatformDeployer object.
        self._parse_cli_options(options)
        self._validate_command()

        # Inspect system; we'll run some system commands differently on Windows.
        self._inspect_system()

        # Inspect project here. If there's anything we can't work with locally,
        #   we want to recognize that now and exit before making any changes
        #   to the project, and before making any remote calls.
        self._inspect_project()

        # Confirm --automate-all, if needed. Currently, this needs to happen before
        #   validate_platform(), because fly_io takes action based on automate_all
        #   in _validate_platform().
        # Then do platform-specific validation.
        self._confirm_automate_all()
        self.platform_deployer.validate_platform()

        # All validation has been completed. Make platform-agnostic modifications.
        # Start with logging.
        if self.log_output:
            self._start_logging()
            # Log the options used for this run.
            self.write_output(f"CLI args: {options}", write_to_console=False)

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


    # --- Internal methods; used only in this class ---

    def _parse_cli_options(self, options):
        """Parse cli options."""

        # Platform-agnostic arguments.
        self.automate_all = options['automate_all']
        self.platform = options['platform']
        
        # This is a True-to-disable option; turn it into a more intuitive flag?
        self.log_output = not(options['no_logging'])
        self.ignore_unclean_git = options['ignore_unclean_git']

        # Platform.sh arguments.
        self.deployed_project_name = options['deployed_project_name']
        self.region = options['region']

        # Developer arguments.
        self.unit_testing = options['unit_testing']
        self.integration_testing = options['integration_testing']


    def _validate_command(self):
        """Make sure the command has been called with a valid set of arguments.
        Returns:
        - None
        - Calls methods that will raise a CommandError if the command is invalid.
        """
        # Right now, we're just validating the platform argument. There will be
        #   more validation, so keep this method in place.
        self._validate_platform_arg()


    def _validate_platform_arg(self):
        """Find out which platform we're targeting, instantiate the
        platform-specific deployer object and platform-specific messages, and 
        get confirmation about using a platform with preliminary support.
        """
        if not self.platform:
            raise CommandError(d_msgs.requires_platform_flag)
        elif self.platform in ['fly_io', 'platform_sh', 'heroku']:
            self.write_output(f"  Deployment target: {self.platform}", skip_logging=True)
        else:
            error_msg = d_msgs.invalid_platform_msg(self.platform)
            raise CommandError(error_msg)

        self.platform_msgs = import_module(f".{self.platform}.deploy_messages", package='simple_deploy.management.commands')

        deployer_module = import_module(f".{self.platform}.deploy", package='simple_deploy.management.commands')
        self.platform_deployer = deployer_module.PlatformDeployer(self)

        try:
            self.platform_deployer.confirm_preliminary()
        except AttributeError:
            # The targeted platform does not have a preliminary warning.
            pass


    def _confirm_automate_all(self):
        """If the --automate-all flag has been passed, confirm that the user
        really wants us to take these actions for them.
        """

        # Placing this test here makes handle() much cleaner.
        if not self.automate_all:
            return

        # Confirm the user knows exactly what will be automated.
        self.write_output(self.platform_msgs.confirm_automate_all, skip_logging=True)
        confirmed = self.get_confirmation(skip_logging=True)

        if confirmed:
            self.write_output("Automating all steps...", skip_logging=True)
        else:
            # Quit and have the user run the command again; don't assume not
            #   wanting to automate means they want to configure.
            self.write_output(d_msgs.cancel_automate_all, skip_logging=True)
            sys.exit()


    def _start_logging(self):
        """Set up for logging."""
        # Create a log directory if needed. Then create the log file, and 
        #   log the creation of the log directory if it happened.
        # In many libraries, one log file is created and then that file is
        #   appended to, and it's on the user to manage log sizes.
        # In this project, the user is expected to run simple_deploy
        #   once, or maybe a couple times if they make a mistake and it exits.
        # So, we should never have runaway log creation. It could be really
        #   helpful to see how many logs are created, and it's also simpler
        #   to review what happened if every log file represents a single run.
        # To create a new log file each time simple_deploy is run, we append
        #   a timestamp to the log filename.
        created_log_dir = self._create_log_dir()

        timestamp = datetime.now().strftime('%Y-%m-%d-%H%M%S')
        log_filename = f"simple_deploy_{timestamp}.log"
        verbose_log_path = self.log_dir_path / log_filename
        verbose_logger = logging.basicConfig(level=logging.INFO,
                filename=verbose_log_path,
                format='%(asctime)s %(levelname)s: %(message)s')

        self.write_output("Logging run of `manage.py simple_deploy`...",
                write_to_console=False)

        if created_log_dir:
            self.write_output(f"Created {self.log_dir_path}.")

        # Make sure we're ignoring sd logs.
        self._ignore_sd_logs()


    def _create_log_dir(self):
        """Create a directory to hold log files, if not already present.
        Returns True if created directory, False if directory was already
          present. Can't log from here, because log file has not been
          created yet.
        """
        self.log_dir_path = settings.BASE_DIR / Path('simple_deploy_logs')
        if not self.log_dir_path.exists():
            self.log_dir_path.mkdir()
            return True
        else:
            return False


    def _ignore_sd_logs(self):
        """Add log dir to .gitignore.
        Adds a .gitignore file if one is not found.
        """
        ignore_msg = "# Ignore logs from simple_deploy."
        ignore_msg += "\nsimple_deploy_logs/\n"

        # Assume .gitignore is in same directory as .git/ directory.
        # gitignore_path = Path(settings.BASE_DIR) / Path('.gitignore')
        gitignore_path = self.git_path / '.gitignore'
        if not gitignore_path.exists():
            # Make the .gitignore file, and add log directory.
            gitignore_path.write_text(ignore_msg)
            self.write_output("No .gitignore file found; created .gitignore.")
            self.write_output("Added simple_deploy_logs/ to .gitignore.")
        else:
            # Append log directory to .gitignore if it's not already there.
            # In r+ mode, a single read moves file pointer to end of file,
            #   setting up for appending.
            with open(gitignore_path, 'r+') as f:
                gitignore_contents = f.read()
                if 'simple_deploy_logs/' not in gitignore_contents:
                    f.write(f"\n{ignore_msg}")
                    self.write_output("Added simple_deploy_logs/ to .gitignore")


    def _strip_secret_key(self, line):
        """Strip secret key value from log file lines."""
        if 'SECRET_KEY:' in line:
            new_line = line.split('SECRET_KEY:')[0]
            new_line += 'SECRET_KEY: *value hidden*'
            return new_line
        else:
            return line


    def _inspect_system(self):
        """Inspect the user's local system for relevant information.

        Currently, we only need to know whether we're on Windows or macOS. The
          first need was just for Windows, which is why the variables are
          self.on_windows rather than something more general like self.user_system.
        Also, keep in mind that we can't use a name like self.platform, because
          platform almost always has a different meaning in this project.

        Some system-specific notes:
        - Some CLI commands are os-specific.
        - Some subsystem calls need to be made a specific way depending on the os.
        """
        self.use_shell = False
        self.on_windows, self.on_macos = False, False
        if os.name == 'nt':
            # DEV: This should use platform.system() as well, but I'm not on Windows
            #   at the moment, so can't test it properly.
            self.on_windows = True
            self.use_shell = True
        elif platform.system() == 'Darwin':
            self.on_macos = True


    def _inspect_project(self):
        """Find out everything we need to know about the project, before
        making any remote calls.

        - Determine project name.
        - Find .git/ directory.
        - Find out if this is a nested project or not.
        - Find significant paths: settings, project root, .git/ location.
        - Get the dependency management approach: requirements.txt, Pipenv, or
            Poetry.
        - Get the current requirements.          

        This method does the minimum introspection needed before making any
          remote calls. Anything that would cause us to exit before making the
          first remote call should be done here.
        """

        # Get project name. There are a number of ways to get the project
        #   name; for now we'll assume the root url config file has not
        #   been moved from the default location.
        # DEV: Use this code when we can require Python >=3.9.
        # self.project_name = settings.ROOT_URLCONF.removesuffix('.urls')
        self.project_name = settings.ROOT_URLCONF.replace('.urls', '')

        # Get project root, from settings.
        #   We wrap this in Path(), because settings files generated before 3.1
        #   had settings.BASE_DIR as a string. Many projects that have been upgraded
        #   to more recent versions may still have this in settings.py.
        # This handles string values for settings.BASE_DIR, and has no impact
        #   when settings.BASE_DIR is already a Path object.
        self.project_root = Path(settings.BASE_DIR)

        # Find .git location, and make sure there's a clean status.
        self._find_git_dir()
        self._check_git_status()

        self.settings_path = f"{self.project_root}/{self.project_name}/settings.py"

        # Find out which package manger is being used: req_txt, poetry, or pipenv
        self.pkg_manager = self._get_dep_man_approach()
        msg = f"  Dependency management system: {self.pkg_manager}"
        self.write_output(msg, skip_logging=True)

        self.requirements = self._get_current_requirements()


    def _find_git_dir(self):
        """Find .git location. Should be in BASE_DIR or BASE_DIR.parent.
        If it's in BASE_DIR.parent, this is a project with a nested
          directory structure.

        This method also sets self.nested_project. A nested project has the
          structure set up by:
           `django-admin startproject project_name`
        A non-nested project has manage.py at the root level, started by:
           `django-admin startproject .`
        This matters for knowing where manage.py is, and knowing where the
         .git dir is likely to be.
        """
        if Path(self.project_root / '.git').exists():
            self.git_path = Path(self.project_root)
            self.write_output(f"  Found .git dir at {self.git_path}.", skip_logging=True)
            self.nested_project = False
        elif (Path(self.project_root).parent / Path('.git')).exists():
            self.git_path = Path(self.project_root).parent
            self.write_output(f"  Found .git dir at {self.git_path}.", skip_logging=True)
            self.nested_project = True
        else:
            error_msg = "Could not find a .git/ directory."
            error_msg += f"\n  Looked in {self.project_root} and in {Path(self.project_root).parent}."
            raise CommandError(error_msg)


    def _check_git_status(self):
        """Make sure we're starting from a clean working state.
        We really want to encourage users to be able to easily undo
          configuration changes. This is especially true for automate-all.

        We do continue work if the only uncommitted change is adding 'simple_deploy'
          to INSTALLED_APPS.

        Returns:
            - None, if we can contine our work.
            - raises CommandError if we shouldn't continue.
        """

        if self.ignore_unclean_git:
            # People can override this check.
            return

        # If 'working tree clean' is in output of `git status`, we can definitely
        #   continue our work.
        cmd = "git status"
        output_obj = self.execute_subp_run(cmd)
        output_str = output_obj.stdout.decode()

        if "working tree clean" in output_str:
            return

        # `git status` indicated that uncommitted changes have been made.
        # Run `git diff`, and see if there are any changes beyond adding
        #   'simple_deploy' to INSTALLED_APPS.
        cmd = "git diff"
        output_obj = self.execute_subp_run(cmd)
        output_str = output_obj.stdout.decode()

        if not self._diff_output_clean(output_str):
            # There are uncommitted changes beyond just adding simple_deploy to
            #   INSTALLED_APPS, so we need to bail.
            error_msg = d_msgs.unclean_git_status
            if self.automate_all:
                error_msg += d_msgs.unclean_git_automate_all
            raise CommandError(error_msg)


    def _diff_output_clean(self, output_str):
        """Check output of `git diff`.
        If there are any lines that start with '- ', that indicates a deletion,
        and we'll bail.

        If there's more than one line starting with '+ ', that indicates more
        than one addition, and we'll bail.

        If there's only one addition, and it's 'simple_deploy' being added to
        INSTALLED_APPS, we can continue.

        Returns:
            - True if output of `git diff` is okay to continue.
            - False if output of `git diff` indicates we should bail.
        """
        num_deletions = output_str.count('\n- ')
        num_additions = output_str.count('\n+ ')

        if (num_deletions > 0) or (num_additions > 1):
            return False

        # There's only one addition. Check if it's anything other than
        #   simple_deploy being added to INSTALLED_APPS.
        # Note: This is not an overly specific test. We're not checking
        #   which file was changed, but there's no real reason someone would add
        #   'simple_deploy' by itself in another file.
        re_diff = r"""(\n\+{1}\s+[',"]simple_deploy[',"],)"""
        m = re.search(re_diff, output_str)
        if m:
            # The only addition was 'simple_deploy', we can move on.
            return True
        else:
            # There was a change, but it wasn't just 'simple_deploy'.
            # We should bail and have user look at their status.
            return False


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
        self.write_output(error_msg, write_to_console=False, skip_logging=True)
        raise CommandError(error_msg)


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
        self.write_output(msg, skip_logging=True)

        if self.pkg_manager == "req_txt":
            requirements = self._get_req_txt_requirements()
        elif self.pkg_manager == "pipenv":
            requirements = self._get_pipfile_requirements()
        elif self.pkg_manager == "poetry":
            requirements = self._get_poetry_requirements()

        # Report findings. 
        msg = "    Found existing dependencies:"
        self.write_output(msg, skip_logging=True)
        for requirement in requirements:
            msg = f"      {requirement}"
            self.write_output(msg, skip_logging=True)

        return requirements


    def _add_simple_deploy_req(self):
        """Add this project to requirements.txt."""
        # Since the simple_deploy app is in INCLUDED_APPS, it needs to be
        #   required. If it's not, Heroku will reject the push.
        # This step isn't needed for Pipenv users, because when they install
        #   django-simple-deploy it's automatically added to Pipfile.
        if self.pkg_manager == "req_txt":
            self.write_output("\n  Looking for django-simple-deploy in requirements.txt...")
            self.add_package('django-simple-deploy')


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


    # --- Methods also used by platform-specific scripts ---

    def write_output(self, output_obj, log_level='INFO',
            write_to_console=True, skip_logging=False):
        """Write output to the appropriate places.
        Output may be a string, or an instance of subprocess.CompletedProcess.

        Need to skip logging before log file is configured.
        """

        # Extract the subprocess output as a string.
        if isinstance(output_obj, subprocess.CompletedProcess):
            # Assume output is either stdout or stderr.
            output_str = output_obj.stdout.decode()
            if not output_str:
                output_str = output_obj.stderr.decode()
        elif isinstance(output_obj, str):
            output_str = output_obj

        # Almost always write to console. Input from prompts is not streamed
        #   because user just typed it into the console.
        if write_to_console:
            self.stdout.write(output_str)

        # Log when appropriate. Log as a series of single lines, for better
        #   log file parsing. 
        if self.log_output and not skip_logging:
            for line in output_str.splitlines():
                # Strip secret key from any line that holds it.
                line = self._strip_secret_key(line)
                logging.info(line)


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
        with subprocess.Popen(cmd_parts, stderr=subprocess.PIPE,
            bufsize=1, universal_newlines=True, shell=self.use_shell) as p:
            for line in p.stderr:
                self.write_output(line, skip_logging=skip_logging)

        if p.returncode != 0:
            raise subprocess.CalledProcessError(p.returncode, p.args)


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
        if not version:
            version = "*"
        new_req_line = f'{package_name} = "{version}"'

        contents = self.pyprojecttoml_path.read_text()
        new_group_string = f"{self.poetry_group_string}{new_req_line}\n"
        contents = contents.replace(self.poetry_group_string, new_group_string)
        self.pyprojecttoml_path.write_text(contents)

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
        self.pyprojecttoml_path.write_text(contents)

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


    def get_confirmation(self, skip_logging=False):
        """Get confirmation for an action.
        This method assumes an appropriate message has already been displayed
          about what is to be done.
        This method shows a yes|no prompt, and returns True or False.
        """
        prompt = "\nAre you sure you want to do this? (yes|no) "
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
            if confirmed.lower() in ('y', 'yes'):
                return True
            elif confirmed.lower() in ('n', 'no'):
                return False
            else:
                self.write_output("  Please answer yes or no.", skip_logging=skip_logging)


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