"""Handles all platform-agnostic aspects of the deployment process."""

# This is the command that's called to automate deployment.
# - It starts the process, and then dispatches to platform-specific helpers.
# - Some of the steps that are platform-agnostic are in this file (at least for now),
#   but are called by the helpers.
# - Each helper gets a reference to this command object.


import sys, os, re, subprocess, logging
from datetime import datetime
from pathlib import Path

from django.core.management.base import BaseCommand, CommandError
from django.conf import settings

from simple_deploy.management.commands.utils import deploy_messages as d_msgs
from simple_deploy.management.commands.utils.deploy_heroku import HerokuDeployer
from simple_deploy.management.commands.utils.deploy_azure import AzureDeployer
from simple_deploy.management.commands.utils.deploy_platformsh import PlatformshDeployer


class Command(BaseCommand):
    """Perform the initial deployment of a simple project.
    Configure as much as possible automatically.
    """

    def add_arguments(self, parser):
        """Define CLI options."""

        parser.add_argument('--automate-all',
            help="Automate all aspects of deployment?",
            action='store_true')

        parser.add_argument('--platform', type=str,
            help="Which platform do you want to deploy to?",
            default='heroku')

        # Default is a free plan, so everyone trying a more expensive plan
        #   is doing so explicitly.
        # If you are testing deployments repeatedly, you'll probably run out
        #   of free minutes.
        # The D1 shared plan won't work, because this script requires a linux
        #   appservice plan. Shared plans are Windows-only.
        # I've been doing most of my testing using the P2V2 plan, which is 
        #   $300/month. At $0.40/hr, my costs have been less than $5 after tens
        #   of deployments, being vigilant about ensuring resources are destroyed
        #   immediately after testing. For testing, also consider:
        #      P1V2, S1, B1.
        # Prices described here are current as of 12/1/2021.
        # See plans at: https://azure.microsoft.com/en-us/pricing/details/app-service/linux/
        parser.add_argument('--azure-plan-sku', type=str,
            help="Which plan sku should be used when creating Azure resources?",
            default='F1')

        # Allow users to skip logging.
        parser.add_argument('--no-logging',
            help="Do you want a record of simple_deploy's output?",
            action='store_true')

        # If we're doing local unit testing, we need to avoid some network
        #   calls.
        parser.add_argument('--local-test',
            help="Used for local unit testing, to avoid network calls.",
            action='store_true')


    def handle(self, *args, **options):
        """Parse options, and dispatch to platform-specific helpers."""
        self.stdout.write("Configuring project for deployment...")

        # Most of the initial work is done in _parse_cli_options(), because
        #   those options affect a lot of what we'll do. For example, we need
        #   to know if we're logging before doing any real work.
        self._parse_cli_options(options)


    def _parse_cli_options(self, options):
        """Parse cli options."""
        self.automate_all = options['automate_all']
        self.platform = options['platform']
        self.azure_plan_sku = options['azure_plan_sku']
        # This is a True-to-disable option; turn it into a more intuitive flag.
        self.log_output = not(options['no_logging'])
        self.local_test = options['local_test']

        if self.log_output:
            self._start_logging()
            # Log the options used for this run.
            self.write_output(f"CLI args: {options}", write_to_console=False)

        # Inspect system; we'll run some system commands differently on Windows.
        self._inspect_system()

        # Inspect project here. If there's anything we can't work with locally,
        #   we want to recognize that now and exit before making any remote calls.
        self._inspect_project()

        if self.automate_all:
            self.write_output("Automating all steps...")
        else:
            self.write_output("Only configuring for deployment...")

        self._check_platform()        


    def _check_platform(self):
        """Find out which platform we're targeting, and call the appropriate
        platform-specific script.
        """
        # DEV: This can be simplified using if self.platform in (target platforms)
        if self.platform == 'heroku':
            self.write_output("  Targeting Heroku deployment...")
            hd = HerokuDeployer(self)
            hd.deploy()
        elif self.platform == 'azure':
            self.write_output("  Targeting Azure deployment...")
            ad = AzureDeployer(self)
            ad.deploy()
        elif self.platform == 'platform_sh':
            self.write_output("  Targeting platform.sh deployment...")
            pl_sh = PlatformshDeployer(self)
            pl_sh.deploy()
        else:
            error_msg = f"The platform {self.platform} is not currently supported."
            self.write_output(error_msg, write_to_console=False)
            raise CommandError(error_msg)


    def _start_logging(self):
        """Set up for logging."""
        # Create a log directory if needed. Then create the log file, and 
        #   log the creation of the log directory if it happened.
        # In many libraries, one log file is created and then that file is
        #   appended to, and it's on the user to manage log sizes.
        # In this project, the user is expected to use run simple_deploy
        #   once, or maybe a couple times if they make a mistake and it exits.
        #   For example, deploying to Azure without --automate-all, or configuring
        #   for Heroku without first running `heroku create`.
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


    def write_output(self, output_obj, log_level='INFO', write_to_console=True):
        """Write output to the appropriate places.
        Output may be a string, or an instance of subprocess.CompletedProcess.
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
        if self.log_output:
            for line in output_str.splitlines():
                # Strip secret key from any line that holds it.
                line = self._strip_secret_key(line)
                logging.info(line)


    def _strip_secret_key(self, line):
        """Strip secret key value from log file lines."""
        if 'SECRET_KEY:' in line:
            new_line = line.split('SECRET_KEY:')[0]
            new_line += 'SECRET_KEY: *value hidden*'
            return new_line
        else:
            return line


    def execute_subp_run_parts(self, cmd_parts):
        """This is similar to execute_subp_run(), but it receives a list of
        command parts rather than a string command. Having this separate method
        is cleaner than having nested if statements in execute_subp_run().

        DEV: May want to make execute_subp_run() examine cmd that's received,
        and dispatch the work based on whether it receives a string or sequence.
        """
        if self.on_windows:
            cmd_string = ' '.join(cmd_parts)
            output = subprocess.run(cmd_string, shell=True, capture_output=True)
        else:
            output = subprocess.run(cmd_parts, capture_output=True)

        return output


    def execute_subp_run(self, cmd):
        """Execute subprocess.run() command.
        We're running commands differently on Windows, so this method
          takes a command and runs it appropriately on each system.
        Returns: output of the command.
        """
        if self.on_windows:
            output = subprocess.run(cmd, shell=True, capture_output=True)
        else:
            cmd_parts = cmd.split()
            output = subprocess.run(cmd_parts, capture_output=True)

        return output


    def execute_command(self, cmd):
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
                self.write_output(line)

        if p.returncode != 0:
            raise subprocess.CalledProcessError(p.returncode, p.args)


    def _inspect_system(self):
        """Find out if we're on Windows, so other methods can run system
        commands appropriately on each system. Note this is the user's system,
        not the host platform we're targeting.
        """
        if os.name == 'nt':
            self.on_windows = True
            self.use_shell = True
        else:
            self.on_windows = False
            self.use_shell = False


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

        # Find .git location.
        self._find_git_dir()

        # Now that we know where git dir is, we can ignore log directory.
        if self.log_output:
            # Make sure log directory is in .gitignore.
            self._ignore_sd_logs()

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
        Assume the .git directory is in the topmost directory; the location
         of .git/ relative to settings.py indicates whether or not this is
         a nested project.
        # DEV: This docstring came from a couple different methods; clean it up.
        """
        if Path(self.project_root / '.git').exists():
            self.git_path = Path(self.project_root)
            self.write_output(f"  Found .git dir at {self.git_path}.")
            self.nested_project = False
        elif (Path(self.project_root).parent / Path('.git')).exists():
            self.git_path = Path(self.project_root).parent
            self.write_output(f"  Found .git dir at {self.git_path}.")
            self.nested_project = True
        else:
            error_msg = "Could not find a .git/ directory."
            error_msg += f"\n  Looked in {self.project_root} and in {Path(self.project_root).parent}."
            self.write_output(error_msg, write_to_console=False)
            raise CommandError(error_msg)


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
            self.write_output(output)
            self.using_req_txt = True

        # Exit if we haven't found any requirements.
        if not any((self.using_req_txt, self.using_pipenv)):
            error_msg = f"Couldn't find any specified requirements in {self.git_path}."
            self.write_output(error_msg, write_to_console=False)
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
            self._add_req_txt_pkg('django-simple-deploy')


    # --- Utility methods ---

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


    def _add_req_txt_pkg(self, package_name):
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


    def _add_pipenv_pkg(self, package_name, version=""):
        """Add a package to Pipfile, if not already present."""
        pkg_present = any(package_name in r for r in self.requirements)

        if pkg_present:
            self.write_output(f"    Found {package_name} in Pipfile.")
        else:
            self._write_pipfile_pkg(package_name, version)


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