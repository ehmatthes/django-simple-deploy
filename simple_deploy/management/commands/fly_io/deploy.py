"""Manages all Fly.io-specific aspects of the deployment process."""

# Note: Internal references to Fly.io will almost always be flyio.
#   Public references, such as the --platform argument, will be fly_io.

import sys, os, re, subprocess, json
from pathlib import Path

from django.conf import settings
from django.core.management.base import CommandError
from django.core.management.utils import get_random_secret_key
from django.utils.crypto import get_random_string
from django.utils.safestring import mark_safe

import requests

from simple_deploy.management.commands import deploy_messages as d_msgs
from simple_deploy.management.commands.fly_io import deploy_messages as flyio_msgs

from simple_deploy.management.commands.utils import write_file_from_template, SimpleDeployCommandError


class PlatformDeployer:
    """Perform the initial deployment of a simple project.
    Configure as much as possible automatically.
    """

    def __init__(self, command):
        """Establishes connection to existing simple_deploy command object."""
        self.sd = command
        self.stdout = self.sd.stdout


    def deploy(self, *args, **options):
        self.sd.write_output("Configuring project for deployment to Fly.io...")

        self._set_on_flyio()
        self._set_debug()

        self._add_dockerfile()
        self._add_dockerignore()
        self._add_flytoml_file()
        self._modify_settings()
        self._add_requirements()

        self._conclude_automate_all()

        self._show_success_message()


    def _set_on_flyio(self):
        """Set a secret, ON_FLYIO. This is used in settings.py to apply
        deployment-specific settings.
        Returns:
        - None
        """
        msg = "Setting ON_FLYIO secret..."
        self.sd.write_output(msg)

        # Skip when unit testing.
        if self.sd.unit_testing:
            msg = "  Skipping for unit testing."
            self.sd.write_output(msg)
            return

        # First check if secret has already been set.
        #   Don't log output of `fly secrets list`!
        cmd = f"fly secrets list -a {self.deployed_project_name}"
        output_obj = self.sd.execute_subp_run(cmd)
        output_str = output_obj.stdout.decode()
        self.sd.log_info(cmd)

        if 'ON_FLYIO' in output_str:
            msg = "  Found ON_FLYIO in existing secrets."
            self.sd.write_output(msg)
            return

        cmd = f"fly secrets set -a {self.deployed_project_name} ON_FLYIO=1"
        output_obj = self.sd.execute_subp_run(cmd)
        output_str = output_obj.stdout.decode()
        self.sd.log_info(cmd)
        self.sd.write_output(output_str)

        msg = "  Set ON_FLYIO secret."
        self.sd.write_output(msg)


    def _set_debug(self):
        """Set a secret, DEBUG=FALSE. This is used in settings.py to apply
        deployment-specific settings.
        Returns:
        - None
        """
        msg = "Setting DEBUG secret..."
        self.sd.write_output(msg)

        # Skip when unit testing.
        if self.sd.unit_testing:
            msg = "  Skipping for unit testing."
            self.sd.write_output(msg)
            return

        # First check if secret has already been set.
        #   Don't log output of `fly secrets list`!
        cmd = f"fly secrets list -a {self.deployed_project_name}"
        output_obj = self.sd.execute_subp_run(cmd)
        output_str = output_obj.stdout.decode()
        self.sd.log_info(cmd)

        if 'DEBUG' in output_str:
            msg = "  Found DEBUG in existing secrets."
            self.sd.write_output(msg)
            return

        cmd = f"fly secrets set -a {self.deployed_project_name} DEBUG=FALSE"
        output_obj = self.sd.execute_subp_run(cmd)
        output_str = output_obj.stdout.decode()
        self.sd.log_info(cmd)
        self.sd.write_output(output_str)

        msg = "  Set DEBUG=FALSE secret."
        self.sd.write_output(msg)


    def _add_dockerfile(self):
        """Add a minimal dockerfile.

        Different dependency management systems need different Dockerfiles.
        We could send an argument to the template to dynamically generate the
          appropriate dockerfile, but that makes the template *much* harder to
          read and reason about. It's much nicer to keep that logic in here, and
          have a couple clean templates that read almost as easily as the final
          dockerfiles that are generated for each dependency management system.

        Returns:
        - path to Dockerfile that was gnerated.
        - None, if an existing Dockerfile was found.
        """

        # File should be in project root, if present.
        self.sd.write_output(f"\n  Looking in {self.sd.git_path} for Dockerfile...")
        dockerfile_present = 'Dockerfile' in os.listdir(self.sd.git_path)

        if dockerfile_present:
            self.sd.write_output("    Found existing Dockerfile.")
        else:
            # Generate file from template.
            self.sd.write_output("    No Dockerfile found. Generating file...")

            context = {
                'django_project_name': self.sd.project_name,
                }

            path = self.sd.project_root / 'Dockerfile'
            if self.sd.pkg_manager == "poetry":
                dockerfile_template = "dockerfile_poetry"
            elif self.sd.pkg_manager == "pipenv":
                dockerfile_template = 'dockerfile_pipenv'
            else:
                dockerfile_template = 'dockerfile'
            write_file_from_template(path, dockerfile_template, context)

            msg = f"\n    Generated Dockerfile: {path}"
            self.sd.write_output(msg)
            return path


    def _add_dockerignore(self):
        """Add a dockerignore file, based on user's local project environmnet.
        Ignore virtual environment dir, system-specific cruft, and IDE cruft.

        If an existing dockerignore is found, make note of that but don't overwrite.

        Returns:
        - True if added dockerignore.
        - False if dockerignore found unnecessary, or if an existing dockerfile
          was found.
        """

        # Check for existing dockerignore file; we're only looking in project root.
        #   If we find one, don't make any changes.
        path = Path('.dockerignore')
        if path.exists():
            msg = "  Found existing .dockerignore file. Not overwriting this file."
            self.sd.write_output(msg)
            return

        # Build dockerignore string.
        dockerignore_str = ""

        # Ignore git repository.
        dockerignore_str += ".git/\n"

        # Ignore venv dir if a venv is active.
        if self.sd.unit_testing:
            venv_dir = 'b_env'
        else:
            venv_dir = os.environ.get("VIRTUAL_ENV")
            
        if venv_dir:
            venv_path = Path(venv_dir)
            dockerignore_str += f"\n{venv_path.name}/\n"


        # Add python cruft.
        dockerignore_str += "\n__pycache__/\n*.pyc\n"

        # Ignore any SQLite databases.
        dockerignore_str += "\n*.sqlite3\n"

        # If on macOS, add .DS_Store.
        if self.sd.on_macos:
            dockerignore_str += "\n.DS_Store\n"

        # Write file.
        path.write_text(dockerignore_str, encoding='utf-8')
        msg = "  Wrote .dockerignore file."
        self.sd.write_output(msg)


    def _add_flytoml_file(self):
        """Add a minimal fly.toml file."""
        # File should be in project root, if present.
        self.sd.write_output(f"\n  Looking in {self.sd.git_path} for fly.toml file...")
        flytoml_present = 'fly.toml' in os.listdir(self.sd.git_path)

        if flytoml_present:
            self.sd.write_output("    Found existing fly.toml file.")
        else:
            # Generate file from template.
            context = {
                'deployed_project_name': self.deployed_project_name,
                'using_pipenv': (self.sd.pkg_manager == "pipenv"),
                }
            path = self.sd.project_root / 'fly.toml'
            write_file_from_template(path, 'fly.toml', context)

            msg = f"\n    Generated fly.toml: {path}"
            self.sd.write_output(msg)
            return path


    def _modify_settings(self):
        """Add settings specific to Fly.io."""
        #   Check if a fly.io section is present. If not, add settings. If already present,
        #   do nothing.
        self.sd.write_output("\n  Checking if settings block for Fly.io present in settings.py...")

        with open(self.sd.settings_path) as f:
            settings_string = f.read()

        if 'if os.environ.get("ON_FLYIO"):' in settings_string:
            self.sd.write_output("\n    Found Fly.io settings block in settings.py.")
            return

        # Add Fly.io settings block.
        self.sd.write_output("    No Fly.io settings found in settings.py; adding settings...")

        safe_settings_string = mark_safe(settings_string)
        context = {
            'current_settings': safe_settings_string,
            'deployed_project_name': self.deployed_project_name,
        }
        path = Path(self.sd.settings_path)
        write_file_from_template(path, 'settings.py', context)

        msg = f"    Modified settings.py file: {path}"
        self.sd.write_output(msg)


    def _add_requirements(self):
        """Add requirements for serving on Fly.io."""
        requirements = ["gunicorn", "psycopg2-binary", "dj-database-url", "whitenoise"]
        self.sd.add_packages(requirements)


    def _conclude_automate_all(self):
        """Finish automating the push to Fly.io.
        - Commit all changes.
        - Call `fly deploy`.
        - Call `fly apps open`, and grab URL.
        """
        # Making this check here lets deploy() be cleaner.
        if not self.sd.automate_all:
            return

        self.sd.commit_changes()

        # Push project.
        # Use execute_command() to stream output of this long-running command.
        self.sd.write_output("  Deploying to Fly.io...")
        cmd = "fly deploy"
        self.sd.log_info(cmd)
        self.sd.execute_command(cmd)

        # Open project.
        self.sd.write_output("  Opening deployed app in a new browser tab...")
        cmd = f"fly apps open -a {self.app_name}"
        output = self.sd.execute_subp_run(cmd)
        self.sd.log_info(cmd)
        self.sd.write_output(output)

        # Get url of deployed project.
        url_re = r'(opening )(http.*?)( \.\.\.)'
        output_str = output.stdout.decode()
        m = re.search(url_re, output_str)
        if m:
            self.deployed_url = m.group(2).strip()


    def _show_success_message(self):
        """After a successful run, show a message about what to do next."""

        # DEV:
        # - Mention that this script should not need to be run again, unless
        #   creating a new deployment.
        #   - Describe ongoing approach of commit, push, migrate. Lots to consider
        #     when doing this on production app with users, make sure you learn.

        if self.sd.automate_all:
            msg = flyio_msgs.success_msg_automate_all(self.deployed_url)
            self.sd.write_output(msg)
        else:
            msg = flyio_msgs.success_msg(log_output=self.sd.log_output)
            self.sd.write_output(msg)


    # --- Methods called from simple_deploy.py ---

    def confirm_preliminary(self):
        """Deployment to Fly.io is in a preliminary state, and we need to be
        explicit about that.
        """
        # Skip this confirmation when unit testing.
        if self.sd.unit_testing:
            return

        self.sd.write_output(flyio_msgs.confirm_preliminary)
        confirmed = self.sd.get_confirmation()

        if confirmed:
            self.sd.write_output("  Continuing with Fly.io deployment...")
        else:
            # Quit and invite the user to try another platform.
            # We are happily exiting the script; there's no need to raise a
            #   CommandError.
            self.sd.write_output(flyio_msgs.cancel_flyio)
            sys.exit()


    def validate_platform(self):
        """Make sure the local environment and project supports deployment to
        Fly.io.
        
        The returncode for a successful command is 0, so anything truthy means
          a command errored out.
        """

        # When running unit tests, will not be logged into CLI.
        if not self.sd.unit_testing:
            self._validate_cli()
            
            self.deployed_project_name = self._get_deployed_project_name()

            # If using automate_all, we need to create the app before creating
            #   the db. But if there's already an app with no deployment, we can 
            #   use that one (maybe created from a previous automate_all run).
            # DEV: Update _get_deployed_project_name() to not throw error if
            #   using automate_all. _create_flyio_app() can exit if not using
            #   automate_all(). If self.deployed_project_name is set, just return
            #   because we'll use that project. If it's not set, call create.
            if not self.deployed_project_name and self.sd.automate_all:
                self.deployed_project_name = self._create_flyio_app()

            # Create the db now, before any additional configuration. Get region
            #   so we know where to create the db.
            self.region = self._get_region()
            self._create_db()
        else:
            self.deployed_project_name = self.sd.deployed_project_name


    def prep_automate_all(self):
        """Take any further actions needed if using automate_all."""
        # All creation has been taken care of earlier, during validation.
        pass


    # --- Helper methods for methods called from simple_deploy.py ---

    def _validate_cli(self):
        """Make sure the Fly.io CLI is installed, and user is logged in."""
        cmd = 'fly version'
        self.sd.log_info(cmd)
        
        # This generates a FileNotFoundError on Ubuntu.
        try:
            output_obj = self.sd.execute_subp_run(cmd)
        except FileNotFoundError:
            raise SimpleDeployCommandError(self.sd, flyio_msgs.cli_not_installed)
        
        self.sd.log_info(output_obj)
        if output_obj.returncode:
            raise SimpleDeployCommandError(self.sd, flyio_msgs.cli_not_installed)
            
        # Check that user is logged in.
        cmd = "fly auth whoami --json"
        self.sd.log_info(cmd)
        output_obj = self.sd.execute_subp_run(cmd)
        if "Error: No access token available. Please login with 'flyctl auth login'" in output_obj.stderr.decode():
            raise SimpleDeployCommandError(self.sd, flyio_msgs.cli_logged_out)
        
        # Show current authenticated fly user.
        whoami_json = json.loads(output_obj.stdout.decode())
        user_email = whoami_json["email"]
        msg = f"  Logged in to Fly.io CLI as: {user_email}"
        self.sd.write_output(msg)
        

    def _get_deployed_project_name(self):
        """Get the Fly.io project name.
        Parse the output of `fly apps list`, and look for apps that have not
          been deployed yet.

        Also, sets self.app_name, so the name can be used here as well.

        Returns:
        - String representing deployed project name.
        - Empty string if no deployed project name found, but using automate_all.
        - Raises CommandError if deployed project name can't be found.
        """
        if self.sd.automate_all:
            # Simply return an empty string to indicate no suitable app was found,
            #   and we'll create one later.
            return ""

        msg = "\nLooking for Fly.io app to deploy against..."
        self.sd.write_output(msg)

        # Get apps info.
        cmd = "fly apps list --json"
        output_obj = self.sd.execute_subp_run(cmd)
        output_str = output_obj.stdout.decode()
        self.sd.log_info(cmd)
        self.sd.log_info(output_str)
        output_json = json.loads(output_str)

        # Only consider projects that have not been deployed yet.
        candidate_apps = [
            app_dict
            for app_dict in output_json
            if not app_dict["Deployed"]
        ]

        # Get all names that might be the app we want to deploy to.
        project_names = [apps_dict["Name"] for apps_dict in candidate_apps]
        project_names = [name for name in project_names if 'builder' not in name]

        # We need to respond according to how many possible names were found.
        if len(project_names) == 0:
            # If no app name found, raise error.
            raise SimpleDeployCommandError(self.sd, flyio_msgs.no_project_name)
        elif len(project_names) == 1:
            # If only one project name, confirm that it's the correct project.
            project_name = project_names[0]
            msg = f"\n*** Found one app on Fly.io: {project_name} ***"
            self.sd.write_output(msg)
            msg = "Is this the app you want to deploy to?"
            if self.sd.get_confirmation(msg):
                self.app_name = project_name
            else:
                raise SimpleDeployCommandError(self.sd, flyio_msgs.no_project_name)
        else:
            # `apps list` does not show much specific inforamtion for undeployed apps.
            #   ie, no creation date, so can't identify most recently created app.
            # Show all undeployed apps, ask user to make selection.
            while True:
                msg = "\n*** Found multiple undeployed apps on Fly.io. ***"
                for index, name in enumerate(project_names):
                    msg += f"\n  {index}: {name}"
                msg += "\n\nYou can cancel this configuration work by entering q."
                msg += "\nWhich app would you like to use? "
                self.sd.log_info(msg)
                selection = input(msg)
                self.sd.log_info(selection)

                if selection.lower() in ['q', 'quit']:
                    raise SimpleDeployCommandError(self.sd, flyio_msgs.no_project_name)

                selected_name = project_names[int(selection)]

                # Confirm selection, because we do *not* want to deploy against
                #   the wrong app.
                msg = f"You have selected {selected_name}. Is that correct?"
                confirmed = self.sd.get_confirmation(msg)
                if confirmed:
                    self.app_name = selected_name
                    break

        # Return deployed app name, or raise CommandError.
        if self.app_name:
            msg = f"  Using Fly.io app: {self.app_name}"
            self.sd.write_output(msg)
            return self.app_name
        else:
            # Can't continue without a Fly.io app to configure against.
            raise SimpleDeployCommandError(self.sd, flyio_msgs.no_project_name)

    def _create_flyio_app(self):
        """Create a new Fly.io app.
        Assumes caller already checked for automate_all, and that a suitable
          app is not already available.
        Returns:
        - String representing new app name.
        - Raises CommandError if an app can't be created.
        """
        msg = "  Creating a new app on Fly.io..."
        self.sd.write_output(msg)

        cmd = "fly apps create --generate-name"
        output_obj = self.sd.execute_subp_run(cmd)
        output_str = output_obj.stdout.decode()
        self.sd.log_info(cmd)
        self.sd.write_output(output_str)

        # Get app name.
        app_name_re = r'(New app created: )(\w+\-\w+\-\d+)'
        self.app_name = ''
        m = re.search(app_name_re, output_str)
        if m:
            self.app_name = m.group(2).strip()

        if self.app_name:
            msg = f"  Created new app: {self.app_name}"
            self.sd.write_output(msg)
            return self.app_name
        else:
            # Can't continue without a Fly.io app to deploy to.
            raise SimpleDeployCommandError(self.sd, flyio_msgs.create_app_failed)


    def _get_region(self):
        """Get the region that the Fly.io app is configured for. We'll need this
        to create a postgres database.

        Notes:
        - V1 `fly apps create` automatically configured a region for the app.
        - In V2, an app doesn't seem to have a region until it's deployed.
        - We need a region to create a db.
        - `fly postgres create` only prompts for a region, there's no -q or -y.
        - `fly postgres create` does highlight nearest region.
        - `fly platform regions` lists available regions, but doesn't identify nearest.
        - So, for now:
          - Default to sea just so deployments work for now. They'll be slow for people
            far from sea.
          - Full fix: Parse `fly platform regions`, present list, ask user to select
            nearest region.

        Current approach:
        - This forum post: https://community.fly.io/t/feature-requests-region-latency-tests/968/6
        - Leads to this tool: https://liveview-counter.fly.dev/
        - It identifies the region with lowest latency, ie "Connected to iad".
        - Solution: request this page, parse for that phrase, select region.
        - Return 'sea' if this doesn't work.

        Returns:
        - String representing region.
        """

        msg = "Looking for Fly.io region..."
        self.sd.write_output(msg)

        # Get region output.
        url = "https://liveview-counter.fly.dev/"
        r = requests.get(url)

        re_region = r'Connected to ([a-z]{3})'
        m = re.search(re_region, r.text)
        if m:
            region = m.group(1)

            msg = f"  Found lowest latency region: {region}"
            self.sd.write_output(msg)
        else:
            region = 'sea'

            msg = f"  Couldn't find lowest latency region, using 'sea'."
            self.sd.write_output(msg)

        return region


    def _create_db(self):
        """Create a db to deploy to.

        An appropriate db should not already exist. We tell people to create
          an app, and then we take care of everything else. We create a db with
          the name app_name-db.
        We will look for a db with that name. If one exists, we'll ask if we
          should use it.
        Otherwise, we'll just create a new db for the app.

        Returns: 
        - None.
        - Raises CommandError if...
        """
        msg = "Looking for a Postgres database..."
        self.sd.write_output(msg)

        db_exists = self._check_if_db_exists()

        if db_exists:
            # A database with the name app_name-db exists.
            # - Is it attached to this app?
            # - Can we use it?
            attached = self._check_db_attached()

            db_name = self.app_name + "-db"
            if attached:
                # Database is attached to this app; get permission to use it.
                msg = flyio_msgs.use_attached_db(db_name, self.db_users)
                self.sd.write_output(msg)

                msg = f"Okay to use {db_name} and proceed?"
                use_db = self.sd.get_confirmation(msg)

                if use_db:
                    # We're going to use this db, and it's already been
                    #   attached. We don't need to do anything further.
                    return
                else:
                    # Permission to use this db denied.
                    # Can't simply create a new db, because the name we'd use
                    #   is already taken.
                    raise SimpleDeployCommandError(self.sd, flyio_msgs.cancel_no_db)
            else:
                # Existing db is not attached; get permission to attach this db.
                msg = flyio_msgs.use_unattached_db(db_name, self.db_users)
                self.sd.write_output(msg)

                msg = f"Okay to use {db_name} and proceed?"
                use_db = self.sd.get_confirmation(msg)

                # Attach db if confirmed.
                if use_db:
                    self._attach_db(db_name)
                    self.db_name = db_name
                    # We're all done.
                    return
                else:
                    # Permission to use this db denied.
                    # Can't simply create a new db, because the name we'd use
                    #   is already taken.
                    raise SimpleDeployCommandError(self.sd, flyio_msgs.cancel_no_db)

        # No usable db found, create a new db.
        msg = f"  Create a new Postgres database..."
        self.sd.write_output(msg)

        self.db_name = f"{self.deployed_project_name}-db"
        cmd = f"fly postgres create --name {self.db_name} --region {self.region}"
        cmd += " --initial-cluster-size 1 --vm-size shared-cpu-1x --volume-size 1"
        self.sd.log_info(cmd)

        # If not using automate_all, make sure it's okay to create a resource
        #   on user's account.
        if not self.sd.automate_all:
            self._confirm_create_db(db_cmd=cmd)

        # Create database.
        # Use execute_command(), to stream output of long-running process.
        # Also, we're not logging this because I believe it contains
        #   db credentials. May want to scrub and then log output.
        self.sd.execute_command(cmd, skip_logging=True)

        msg = "  Created Postgres database."
        self.sd.write_output(msg)

        self._attach_db(self.db_name)

    def _attach_db(self, db_name):
        """Attach the database to the app."""
        # Run `attach` command (and confirm DATABASE_URL is set?)
        msg = "  Attaching database to Fly.io app..."
        self.sd.write_output(msg)
        cmd = f"fly postgres attach --app {self.deployed_project_name} {db_name}"
        self.sd.log_info(cmd)

        output_obj = self.sd.execute_subp_run(cmd)
        output_str = output_obj.stdout.decode()
        self.sd.write_output(output_str)

        msg = "  Attached database to app."
        self.sd.write_output(msg)

    def _check_if_db_exists(self):
        """Check if a postgres db already exists that should be used with this app.
        Returns:
        - True if db found.
        - False if not found.
        """

        # First, see if any Postgres clusters exist.
        cmd = "fly postgres list --json"
        output_obj = self.sd.execute_subp_run(cmd)
        output_str = output_obj.stdout.decode()
        self.sd.log_info(cmd)
        self.sd.log_info(output_str)

        if "No postgres clusters found" in output_str:
            return False

        # There are some Postgres dbs. Get their names.
        pg_names = [
            pg_dict["Name"]
            for pg_dict in json.loads(output_str)
        ]

        # See if any of these names match this app.
        usable_pg_name = self.app_name + "-db"
        if usable_pg_name in pg_names:
            msg = f"  Postgres db found: {usable_pg_name}"
            self.sd.write_output(msg)
            return True
        else:
            msg = "  No matching Postgres database found."
            self.sd.write_output(msg)
            return False

    def _check_db_attached(self):
        """Check if the db that was found is attached to this app.

        Database is considered attached to this app it has a user with the same
          name as the app, using underscores instead of hyphens.
        This is the default behavior if you create a new app, then a new db,
          then attach the db to that app.

        Returns:
        - True if db attached to this app.
        - False if db not attached to this app.
        - Raises SimpleDeployCommandError if we can't find a reason to use the db.

        Also, defines self.db_users, which can be used in subsequent messages.
        """
        # Get users of this db.
        #   `fly postgres users list` does not accept `--json` flag. :/
        db_name = self.app_name + "-db"
        cmd = f"fly postgres users list -a {db_name}"
        output_obj = self.sd.execute_subp_run(cmd)
        output_str = output_obj.stdout.decode()
        self.sd.log_info(cmd)
        self.sd.log_info(output_str)

        # Break output into lines, get rid of header line.
        lines = output_str.split("\n")[1:]
        # Get rid of blank lines.
        lines = [line for line in lines if line]
        # Pull user from each line.
        self.db_users = []
        for line in lines:
            # user is everything before first tab.
            tab_index = line.find("\t")
            user = line[:tab_index].strip()
            self.db_users.append(user)

        self.sd.log_info(f"DB users: {self.db_users}")

        default_users = {'flypgadmin', 'postgres', 'repmgr'}
        app_user = self.app_name.replace('-', '_')
        if set(self.db_users) == default_users:
            # This db only has default users set when a fresh db is made.
            #   Assume it's unattached.
            return False
        elif (app_user in self.db_users) and (len(self.db_users) == 4):
            # The current remote app has been attached to this db.
            #   Will still need confirmation we can use this db.
            return True
        else:
            # This db has more than the default users, and not just the
            #   current app. Let's not touch it.
            # If anyone hits this situation and we should proceed, we'll
            #   revisit this block.
            # Note: This path has only been tested once, by manually adding
            #   "dummy-user" to the list of db users."
            msg = flyio_msgs.cant_use_db(db_name, self.db_users)
            raise SimpleDeployCommandError(self.sd, msg)

    def _confirm_create_db(self, db_cmd):
        """We really need to confirm that the user wants a db created on their behalf.
        Show the command that will be run on the user's behalf.
        Returns:
        - True if confirmed.
        - Raises CommandError if not confirmed.
        """
        if self.sd.unit_testing:
            return

        self.stdout.write(flyio_msgs.confirm_create_db(db_cmd))
        confirmed = self.sd.get_confirmation()

        if confirmed:
            self.stdout.write("  Creating database...")
        else:
            # Quit and invite the user to create a database manually.
            raise SimpleDeployCommandError(self.sd, flyio_msgs.cancel_no_db)
