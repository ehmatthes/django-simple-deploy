"""Handles all platform-agnostic aspects of the deployment process."""

# This is the command that's called to automate deployment.
# - It starts the process, and then dispatches to platform-specific helpers.
# - Each helper gets a reference to this command object.


import sys, os, platform, re, subprocess, logging
from datetime import datetime
from pathlib import Path

from django.core.management.base import BaseCommand, CommandError
from django.conf import settings

from simple_deploy.management.commands.utils import deploy_messages as d_msgs
from simple_deploy.management.commands.utils import deploy_messages_heroku as dh_msgs
from simple_deploy.management.commands.utils import deploy_messages_platformsh as plsh_msgs
from simple_deploy.management.commands.utils import deploy_messages_flyio as flyio_msgs

from simple_deploy.management.commands.utils.deploy_heroku import HerokuDeployer
from simple_deploy.management.commands.utils.deploy_platformsh import PlatformshDeployer
from simple_deploy.management.commands.utils.deploy_flyio import FlyioDeployer


class Command(BaseCommand):
    """Perform the initial deployment of a simple project.
    Configure as much as possible automatically.
    """

    def add_arguments(self, parser):
        """Define CLI options."""

        # --- Platform-agnostic arguments ---

        parser.add_argument('--automate-all',
            help="Automate all aspects of deployment?",
            action='store_true')

        parser.add_argument('--platform', type=str,
            help="Which platform do you want to deploy to?",
            default='')

        # Allow users to skip logging.
        parser.add_argument('--no-logging',
            help="Do you want a record of simple_deploy's output?",
            action='store_true')

        # Allow users to use simple_deploy even with an unclean git status.
        parser.add_argument('--ignore-unclean-git',
            help="Run simple_deploy even with an unclean `git status` message.",
            action='store_true')

        # --- Platform.sh arguments ---

        # Allow users to set the deployed project name. This is the name that
        #   will be used by the platform, which may be different than the name
        #   used in the `startproject` command. See the Platform.sh script
        #   for use of this flag.
        parser.add_argument('--deployed-project-name', type=str,
            help="What name should the platform use for this project?\n(This is normally discovered automatically through inspection.)",
            default='')

        # Allow users to specify the region for a project when using --automate-all.
        parser.add_argument('--region', type=str,
            help="Which region do you want to deploy to?",
            default='us-3.platform.sh')

        # --- Developer arguments ---

        # If we're doing local unit testing, we need to avoid some network
        #   calls.
        parser.add_argument('--unit-testing',
            help="Used for local unit testing, to avoid network calls.",
            action='store_true')

        parser.add_argument('--integration-testing',
            help="Used for integration testing, to avoid confirmations.",
            action='store_true')


    def handle(self, *args, **options):
        """Parse options, and dispatch to platform-specific helpers."""
        self.stdout.write("Configuring project for deployment...")

        # Parse CLI options, and validate the set of arguments we've been given.
        self._parse_cli_options(options)
        self._validate_command()

        # Inspect system; we'll run some system commands differently on Windows.
        self._inspect_system()

        # Inspect project here. If there's anything we can't work with locally,
        #   we want to recognize that now and exit before making any changes
        #   to the project, and before making any remote calls.
        self._inspect_project()

        # Confirm --automate-all, if needed. Currently, this needs to happen before
        #   _validate_platform(), because fly_io takes action based on automate_all
        #   in _validate_platform().
        # Then build the platform-specifc deployer instance, and do platform-specific
        #   validation. 
        self._confirm_automate_all()
        self._validate_platform()

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

        # During development, sometimes helpful to exit before calling deploy().
        # print('bye')
        # sys.exit()

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
        """
        if not self.platform:
            self.write_output(d_msgs.requires_platform_flag, write_to_console=False)
            raise CommandError(d_msgs.requires_platform_flag)


    def _validate_platform(self):
        """Find out which platform we're targeting, and instantiate the
        platform-specific deployer object. Also, call any necessary
        platform-specific validation and confirmation methods here.
        """
        if self.platform == 'heroku':
            self.write_output("  Targeting Heroku deployment...", skip_logging=True)
            self.platform_deployer = HerokuDeployer(self)
        elif self.platform == 'platform_sh':
            self.write_output("  Targeting platform.sh deployment...", skip_logging=True)
            self.platform_deployer = PlatformshDeployer(self)
            self.platform_deployer.confirm_preliminary()
        elif self.platform == 'fly_io':
            self.write_output("  Targeting Fly.io deployment...", skip_logging=True)
            self.platform_deployer = FlyioDeployer(self)
            self.platform_deployer.confirm_preliminary()
        else:
            error_msg = f"The platform {self.platform} is not currently supported."
            raise CommandError(error_msg)

        self.platform_deployer.validate_platform()


    def _confirm_automate_all(self):
        """If the --automate-all flag has been passed, confirm that the user
        really wants us to take these actions for them.
        """

        # Placing this test here makes handle() much cleaner.
        if not self.automate_all:
            return

        # Confirm the user knows exactly what will be automated; this
        #   message is specific to each platform.
        if self.platform == 'heroku':
            msg = dh_msgs.confirm_automate_all
        elif self.platform == 'platform_sh':
            msg = plsh_msgs.confirm_automate_all
        elif self.platform == 'fly_io':
            msg = flyio_msgs.confirm_automate_all
        else:
            # The platform name is not valid!
            # DEV: This should be removed when the logic around when to call
            #   _validate_platform() has been cleaned up.
            # See issue #120: https://github.com/ehmatthes/django-simple-deploy/issues/120
            error_msg = f"The platform {self.platform} is not currently supported."
            raise CommandError(error_msg)

        self.write_output(msg, skip_logging=True)
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
        self.project_root = settings.BASE_DIR

        # Find .git location, and make sure there's a clean status.
        self._find_git_dir()
        self._check_git_status()

        self.settings_path = f"{self.project_root}/{self.project_name}/settings.py"

        self._get_dep_man_approach()
        self._get_current_requirements()


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
        """

        # In a simple project, I don't think we should find both Pipfile
        #   and requirements.txt. However, if there's both, prioritize Pipfile.
        self.using_req_txt = 'requirements.txt' in os.listdir(self.git_path)

        # DEV: If both req_txt and Pipfile are found, could just use req.txt.
        #      That's Heroku's prioritization, I believe. Address this if
        #      anyone has such a project, and ask why they have both initially.
        self.using_pipenv = 'Pipfile' in os.listdir(self.git_path)
        if self.using_pipenv:
            self.using_req_txt = False

        self.using_poetry = 'pyproject.toml' in os.listdir(self.git_path)
        if self.using_poetry:
            # Heroku does not recognize pyproject.toml, so we'll export to
            #   a requirements.txt file, and then work from that. This should
            #   not affect the user's local environment.
            cmd = 'poetry export -f requirements.txt --output requirements.txt --without-hashes'
            output = self.execute_subp_run(cmd)
            self.write_output(output, skip_logging=True)
            self.using_req_txt = True

        # Exit if we haven't found any requirements.
        if not any((self.using_req_txt, self.using_pipenv)):
            error_msg = f"Couldn't find any specified requirements in {self.git_path}."
            self.write_output(error_msg, write_to_console=False, skip_logging=True)
            raise CommandError(error_msg)


    def _get_current_requirements(self):
        """Get current project requirements, before adding any new ones.
        """
        if self.using_req_txt:
            # Build path to requirements.txt.
            self.req_txt_path = f"{self.git_path}/requirements.txt"

            # Get list of requirements, with versions.
            with open(f"{self.git_path}/requirements.txt") as f:
                requirements = f.readlines()
                self.requirements = [r.rstrip() for r in requirements]

        if self.using_pipenv:
            # Build path to Pipfile.
            self.pipfile_path = f"{self.git_path}/Pipfile"

            # Get list of requirements.
            self.requirements = self._get_pipfile_requirements()


    def _add_simple_deploy_req(self):
        """Add this project to requirements.txt."""
        # Since the simple_deploy app is in INCLUDED_APPS, it needs to be
        #   required. If it's not, Heroku will reject the push.
        # This step isn't needed for Pipenv users, because when they install
        #   django-simple-deploy it's automatically added to Pipfile.
        if self.using_req_txt:
            self.write_output("\n  Looking for django-simple-deploy in requirements.txt...")
            self.add_req_txt_pkg('django-simple-deploy')


    def _get_pipfile_requirements(self):
        """Get a list of requirements that are already in the Pipfile."""
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


    def execute_subp_run_parts(self, cmd_parts):
        """This is similar to execute_subp_run(), but it receives a list of
        command parts rather than a string command. Having this separate method
        is cleaner than having nested if statements in execute_subp_run().

        Currently this is used to issue a git commit command, where running
          cmd.split() would split on the commit message.

        DEV: May want to make execute_subp_run() examine cmd that's received,
        and dispatch the work based on whether it receives a string or sequence.
        """
        if self.on_windows:
            cmd_string = ' '.join(cmd_parts)
            output = subprocess.run(cmd_string, shell=True, capture_output=True)
        else:
            output = subprocess.run(cmd_parts, capture_output=True)

        return output


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
            - if check=True is passed, raises CalledProcessError. 
        """
        if self.on_windows:
            output = subprocess.run(cmd, shell=True, capture_output=True)
        else:
            cmd_parts = cmd.split()
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
        #   now that's only the `git push heroku` call. That call writes to
        #   stderr; I'm not sure how to stream both stdout and stderr.
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


    def add_req_txt_pkg(self, package_name):
        """Add a package to requirements.txt, if not already present."""
        root_package_name = package_name.split('<')[0]

        # Note: This does not check for specific versions. It gives priority
        #   to any version already specified in requirements.
        pkg_present = any(root_package_name in r for r in self.requirements)

        if pkg_present:
            self.write_output(f"    Found {root_package_name} in requirements file.")
        else:
            with open(self.req_txt_path, 'a') as f:
                # Align comments, so we don't make req_txt file ugly.
                #   Version specs are in package_name in req_txt approach.
                tab_string = ' ' * (30 - len(package_name))
                f.write(f"\n{package_name}{tab_string}# Added by simple_deploy command.")

            self.write_output(f"    Added {package_name} to requirements.txt.")


    def add_pipenv_pkg(self, package_name, version=""):
        """Add a package to Pipfile, if not already present."""
        pkg_present = any(package_name in r for r in self.requirements)

        if pkg_present:
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
        # If we write this command as a string, the commit message will be split
        #   incorrectly.
        cmd_parts = ['git', 'commit', '-am', '"Configured project for deployment."']
        output = self.execute_subp_run_parts(cmd_parts)
        self.write_output(output)
