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


    def handle(self, *args, **options):
        """Parse options, and dispatch to platform-specific helpers."""
        self.stdout.write("Configuring project for deployment...")
        self._parse_cli_options(options)


    def _parse_cli_options(self, options):
        """Parse cli options."""
        self.automate_all = options['automate_all']
        self.platform = options['platform']
        self.azure_plan_sku = options['azure_plan_sku']
        # This is a True-to-disable option; turn it into a more intuitive flag.
        self.log_output = not(options['no_logging'])

        if self.log_output:
            self._start_logging()
            # Log the options used for this run.
            self.write_output(f"CLI args: {options}", write_to_console=False)

        if self.automate_all:
            self.write_output("Automating all steps...")
        else:
            self.write_output("Only configuring for deployment...")

        if self.platform == 'heroku':
            self.write_output("  Targeting Heroku deployment...")
            hd = HerokuDeployer(self)
            hd.deploy()
        elif self.platform == 'azure':
            self.write_output("  Targeting Azure deployment...")
            ad = AzureDeployer(self)
            ad.deploy()
        else:
            error_msg = f"The platform {self.platform} is not currently supported."
            self.write_output(error_msg)
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

        # Make sure log directory is in .gitignore.
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

        gitignore_path = Path(settings.BASE_DIR) / Path('.gitignore')
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
                    f.write(f"\n\n{ignore_msg}")
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
            bufsize=1, universal_newlines=True) as p:
            for line in p.stderr:
                self.write_output(line)

        if p.returncode != 0:
            raise CalledProcessError(p.returncode, p.args)


    def _inspect_project(self):
        """Inspect the project, and pull information needed by multiple steps.
        """

         # Get project name. There are a number of ways to get the project
        #   name; for now we'll assume the root url config file has not
        #   been moved from the default location.
        # DEV: Use this code when we can require Python >=3.9.
        # self.project_name = settings.ROOT_URLCONF.removesuffix('.urls')
        self.project_name = settings.ROOT_URLCONF.replace('.urls', '')

        self.project_root = settings.BASE_DIR
        self.settings_path = f"{self.project_root}/{self.project_name}/settings.py"

        self._get_dep_man_approach()
        self._get_current_requirements()


    def _get_dep_man_approach(self):
        """Identify which dependency management approach the project uses.
        req_txt, poetry, or pipenv.
        """

        # In a simple project, I don't think we should find both Pipfile
        #   and requirements.txt. However, if there's both, prioritize Pipfile.
        self.using_req_txt = 'requirements.txt' in os.listdir(self.project_root)

        # DEV: If both req_txt and Pipfile are found, could just use req.txt.
        #      That's Heroku's prioritization, I believe. Address this if
        #      anyone has such a project, and ask why they have both initially.
        self.using_pipenv = 'Pipfile' in os.listdir(self.project_root)
        if self.using_pipenv:
            self.using_req_txt = False

        self.using_poetry = 'pyproject.toml' in os.listdir(self.project_root)
        if self.using_poetry:
            # Heroku does not recognize pyproject.toml, so we'll export to
            #   a requirements.txt file, and then work from that. This should
            #   not affect the user's local environment.
            export_cmd_parts = ['poetry', 'export', '-f', 'requirements.txt',
                    '--output', 'requirements.txt', '--without-hashes']
            output = subprocess.run(export_cmd_parts, capture_output=True)
            self.write_output(output)
            self.using_req_txt = True


    def _get_current_requirements(self):
        """Get current project requirements, before adding any new ones.
        """
        if self.using_req_txt:
            # Build path to requirements.txt.
            self.req_txt_path = f"{self.project_root}/requirements.txt"

            # Get list of requirements, with versions.
            with open(f"{self.project_root}/requirements.txt") as f:
                requirements = f.readlines()
                self.requirements = [r.rstrip() for r in requirements]

        if self.using_pipenv:
            # Build path to Pipfile.
            self.pipfile_path = f"{self.project_root}/Pipfile"

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