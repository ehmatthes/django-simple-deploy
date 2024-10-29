"""Manages all Fly.io-specific aspects of the deployment process.

Notes:
- Internal references to Fly.io will almost always be flyio. Public references, such as
  the --platform argument, will be fly_io.
- self.deployed_project_name and self.app_name are identical. The first is used in the
  simple_deploy CLI, but Fly refers to "apps" in their docs. This redundancy makes it
  easier to code Fly CLI commands.
"""

import sys, os, re, json
from pathlib import Path

from django.utils.safestring import mark_safe

import httpx

from . import deploy_messages as platform_msgs

from ..utils import plugin_utils


class PlatformDeployer:
    """Perform the initial deployment to Fly.io

    If --automate-all is used, carry out an actual deployment.
    If not, do all configuration work so the user only has to commit changes, and call
    `fly deploy`.
    """

    def __init__(self, sd_config):
        """Receives config info about user's system, and this run of simple_deploy."""
        self.sd_config = sd_config
        self.stdout = self.sd_config.stdout
        self.templates_path = Path(__file__).parent / "templates"

    # --- Public methods ---

    def deploy(self, *args, **options):
        """Coordinate the overall configuration and deployment."""
        plugin_utils.write_output(
            self.sd_config, "\nConfiguring project for deployment to Fly.io..."
        )

        self._validate_platform()

        self._prep_automate_all()
        self._set_env_vars()
        self._add_dockerfile()
        self._add_dockerignore()
        self._add_flytoml()
        self._modify_settings()
        self._add_requirements()

        self._conclude_automate_all()
        self._show_success_message()

    # --- Helper methods for deploy() ---

    def _validate_platform(self):
        """Make sure the local environment and project supports deployment to Fly.io.

        Make sure CLI is installed, and user is authenticated. Make sure necessary
        resources have been created and identified, and that we have the user's
        permission to use those resources.

        Returns:
            None

        Raises:
            SimpleDeployCommandError: If we find any reason deployment won't work.
        """
        if self.sd_config.unit_testing:
            # Unit tests don't use the platform's CLI. Use the deployed project name
            # that was passed to the simple_deploy CLI.
            self.deployed_project_name = self.sd_config.deployed_project_name
            return

        self._check_flyio_settings()
        self._validate_cli()

        # Make sure a Fly.io app has been created, or create one if  using
        # --automate-all. Get the name of that app, which will be the  same as
        # self.app_name.
        self.deployed_project_name = self._get_deployed_project_name()

        # Create the db now, before any additional configuration.
        self._create_db()

    def _prep_automate_all(self):
        """Take any further actions needed if using automate_all."""
        # All necessary resources have been created earlier, during validation.
        pass

    def _set_env_vars(self):
        """Set Fly.io-specific environment variables."""
        if self.sd_config.unit_testing:
            return

        self._set_on_flyio()
        self._set_debug()

    def _set_on_flyio(self):
        """Set a secret, ON_FLYIO. This is used in settings.py to apply
        deployment-specific settings.
        """
        msg = "\nSetting ON_FLYIO secret..."
        plugin_utils.write_output(self.sd_config, msg)
        self._set_secret("ON_FLYIO", "ON_FLYIO=1")

    def _set_debug(self):
        """Set a secret, DEBUG=FALSE. This is used in settings.py to apply
        deployment-specific settings.
        """
        msg = "Setting DEBUG secret..."
        plugin_utils.write_output(self.sd_config, msg)
        self._set_secret("DEBUG", "DEBUG=FALSE")

    def _add_dockerfile(self):
        """Add a minimal dockerfile.

        Different dependency management systems need different Dockerfiles. We could
        send an argument to the template to dynamically generate the appropriate
        dockerfile, but that makes the template *much* harder to read and reason about.
        It's much nicer to keep that logic in here, and have a couple clean templates
        that read almost as easily as the final dockerfiles that are generated for each
        dependency management system.
        """

        # Build file contents from template and context.
        if self.sd_config.pkg_manager == "poetry":
            dockerfile_template = "dockerfile_poetry"
        elif self.sd_config.pkg_manager == "pipenv":
            dockerfile_template = "dockerfile_pipenv"
        else:
            dockerfile_template = "dockerfile"
        template_path = self.templates_path / dockerfile_template

        context = {
            "django_project_name": self.sd_config.local_project_name,
        }

        contents = plugin_utils.get_template_string(template_path, context)

        # Write file to project.
        path = self.sd_config.project_root / "Dockerfile"
        plugin_utils.add_file(self.sd_config, path, contents)

    def _add_dockerignore(self):
        """Add a dockerignore file, based on user's local project environmnet.
        Ignore virtual environment dir, system-specific cruft, and IDE cruft.
        """
        path = self.sd_config.project_root / ".dockerignore"
        dockerignore_str = self._build_dockerignore()
        plugin_utils.add_file(self.sd_config, path, dockerignore_str)

    def _add_flytoml(self):
        """Add a minimal fly.toml file."""

        # Build contents of fly.toml.
        template_path = self.templates_path / "fly.toml"
        context = {
            "deployed_project_name": self.deployed_project_name,
            "using_pipenv": (self.sd_config.pkg_manager == "pipenv"),
        }
        contents = plugin_utils.get_template_string(template_path, context)

        # Write file to project.
        path = self.sd_config.project_root / "fly.toml"
        plugin_utils.add_file(self.sd_config, path, contents)

    def _modify_settings(self):
        """Add platformsh-specific settings."""
        # Get modified version of settings.
        template_path = self.templates_path / "settings.py"

        settings_string = self.sd_config.settings_path.read_text()
        safe_settings_string = mark_safe(settings_string)
        context = {
            "current_settings": safe_settings_string,
            "deployed_project_name": self.deployed_project_name,
        }

        modified_settings_string = plugin_utils.get_template_string(
            template_path, context
        )

        # Write settings to file.
        plugin_utils.modify_file(
            self.sd_config, self.sd_config.settings_path, modified_settings_string
        )

    def _add_requirements(self):
        """Add requirements for deploying to Fly.io."""
        requirements = ["gunicorn", "psycopg2-binary", "dj-database-url", "whitenoise"]
        plugin_utils.add_packages(self.sd_config, requirements)

    def _conclude_automate_all(self):
        """Finish automating the push to Fly.io.

        - Commit all changes.
        - Call `fly deploy`.
        - Call `fly apps open`, and grab URL.
        """
        # Making this check here lets deploy() be cleaner.
        if not self.sd_config.automate_all:
            return

        plugin_utils.commit_changes(self.sd_config)

        # Push project.
        plugin_utils.write_output(self.sd_config, "  Deploying to Fly.io...")
        cmd = "fly deploy"
        plugin_utils.run_slow_command(self.sd_config, cmd)

        # Open project.
        plugin_utils.write_output(
            self.sd_config, "  Opening deployed app in a new browser tab..."
        )
        cmd = f"fly apps open -a {self.app_name}"
        output = plugin_utils.run_quick_command(self.sd_config, cmd)
        plugin_utils.write_output(self.sd_config, output)

        # Get URL of deployed project.
        url_re = r"(opening )(http.*?)( \.\.\.)"
        output_str = output.stdout.decode()
        m = re.search(url_re, output_str)
        if m:
            self.deployed_url = m.group(2).strip()

    def _show_success_message(self):
        """After a successful run, show a message about what to do next.

        Describe ongoing approach of commit, push, migrate.
        """
        if self.sd_config.automate_all:
            msg = platform_msgs.success_msg_automate_all(self.deployed_url)
        else:
            msg = platform_msgs.success_msg(log_output=self.sd_config.log_output)
        plugin_utils.write_output(self.sd_config, msg)

    def _set_secret(self, needle, secret):
        """Set a secret on Fly, if it's not already set.

        DEV: Do we need to say that it's already set, and get confirmation to change
        value? (Only needed if it's not set to same value.)
        """

        # First check if secret has already been set.
        #   Don't log output of `fly secrets list`!
        cmd = f"fly secrets list -a {self.deployed_project_name} --json"
        output_obj = plugin_utils.run_quick_command(self.sd_config, cmd)
        secrets_json = json.loads(output_obj.stdout.decode())

        secrets_keys = [secret["Name"] for secret in secrets_json]

        if needle in secrets_keys:
            msg = f"  Found {needle} in existing secrets."
            plugin_utils.write_output(self.sd_config, msg)
            return

        cmd = f"fly secrets set -a {self.deployed_project_name} {secret}"
        output_obj = plugin_utils.run_quick_command(self.sd_config, cmd)
        output_str = output_obj.stdout.decode()
        plugin_utils.write_output(self.sd_config, output_str)

        msg = f"  Set secret: {secret}"
        plugin_utils.write_output(self.sd_config, msg)

    def _build_dockerignore(self):
        """Build the contents of the dockerignore file."""

        # Start with git repository.
        dockerignore_str = ".git/\n"

        # Ignore venv dir if a venv is active.
        if self.sd_config.unit_testing:
            # Unit tests build a venv dir, but use the direct path to the venv. They
            # don't run in an active venv.
            venv_dir = "b_env"
        else:
            venv_dir = os.environ.get("VIRTUAL_ENV")

        if venv_dir:
            venv_path = Path(venv_dir)
            dockerignore_str += f"\n{venv_path.name}/\n"

        # Ignore Python stuff, SQLite db.
        dockerignore_str += "\n__pycache__/\n*.pyc\n\n*.sqlite3\n"

        # If on macOS, ignore .DS_Store.
        if self.sd_config.on_macos:
            dockerignore_str += "\n.DS_Store\n"

        return dockerignore_str

    # --- Helper methods for _validate_platform() ---

    def _check_flyio_settings(self):
        """Check to see if a Fly.io settings block already exists."""
        start_line = "# Fly.io settings."
        plugin_utils.check_settings(
            self.sd_config,
            "Fly.io",
            start_line,
            platform_msgs.flyio_settings_found,
            platform_msgs.cant_overwrite_settings,
        )

    def _validate_cli(self):
        """Make sure the Fly.io CLI is installed, and user is authenticated."""
        cmd = "fly version"

        # This generates a FileNotFoundError on Ubuntu if the CLI is not installed.
        try:
            output_obj = plugin_utils.run_quick_command(self.sd_config, cmd)
        except FileNotFoundError:
            raise plugin_utils.SimpleDeployCommandError(
                self.sd_config, platform_msgs.cli_not_installed
            )

        plugin_utils.log_info(self.sd_config, output_obj)

        # DEV: Note which OS this block runs on; I believe it's macOS.
        if output_obj.returncode:
            raise plugin_utils.SimpleDeployCommandError(
                self.sd_config, platform_msgs.cli_not_installed
            )

        # Check that user is authenticated.
        cmd = "fly auth whoami --json"
        output_obj = plugin_utils.run_quick_command(self.sd_config, cmd)

        error_msg = "Error: No access token available."
        if error_msg in output_obj.stderr.decode():
            raise plugin_utils.SimpleDeployCommandError(
                self.sd_config, platform_msgs.cli_logged_out
            )

        # Show current authenticated fly user.
        whoami_json = json.loads(output_obj.stdout.decode())
        user_email = whoami_json["email"]
        msg = f"  Logged in to Fly.io CLI as: {user_email}"
        plugin_utils.write_output(self.sd_config, msg)

    def _get_deployed_project_name(self):
        """Get the Fly.io project name.

        Parse the output of `fly apps list`, and look for apps that have not
        been deployed yet. Note there's some ambiguity between the use of
        "project name" and "app name". This comes from usage in both Django
        and target platforms. Also note that database apps can't be easily
        distinguished from other apps.

        During automated runs, creates a new Fly app if there isn't one we can use.

        User interactions:
        - If one app found, prompts user to confirm correct app.
        - If multiple apps found, prompts user to select correct one.

        Sets:
            str: self.app_name

        Returns:
            str: The deployed project name (self.app_name). Empty string if
            using --automate-all.

        Raises:
            SimpleDeployCommandError: If deployed project name can't be found.
        """
        msg = "\nLooking for Fly.io app to deploy against..."
        plugin_utils.write_output(self.sd_config, msg)

        # Get info about user's apps on Fly.io.
        cmd = "fly apps list --json"

        # Run command, and get json output.
        # CLI has been validated; should not have to deal with stderr.
        output_str = plugin_utils.run_quick_command(self.sd_config, cmd).stdout.decode()
        plugin_utils.log_info(self.sd_config, output_str)
        output_json = json.loads(output_str)

        project_names = self._get_undeployed_projects(output_json)
        self._select_project_name(project_names)

        # Display and return deployed app name.
        msg = f"  Using Fly.io app: {self.app_name}"
        plugin_utils.write_output(self.sd_config, msg)
        return self.app_name

    def _get_undeployed_projects(self, output_json):
        """Identify fly apps that have not yet been deployed to."""
        candidate_apps = [
            app_dict for app_dict in output_json if not app_dict["Deployed"]
        ]

        # Remove all apps with 'builder' in name.
        project_names = [
            apps_dict["Name"]
            for apps_dict in candidate_apps
            if "builder" not in apps_dict["Name"]
        ]

        return project_names

    def _select_project_name(self, project_names):
        """Select the correct project to deploy to."""

        if not project_names:
            # No app name found.
            if self.sd_config.automate_all:
                self.app_name = self._create_flyio_app()
            else:
                raise plugin_utils.SimpleDeployCommandError(
                    self.sd_config, platform_msgs.no_project_name
                )
        elif len(project_names) == 1:
            # Only one app name found. Confirm we can deploy to this app.
            project_name = project_names[0]
            msg = f"\n*** Found one undeployed app on Fly.io: {project_name} ***"
            plugin_utils.write_output(self.sd_config, msg)

            prompt = "Is this the app you want to deploy to?"
            if plugin_utils.get_confirmation(self.sd_config, prompt):
                self.app_name = project_name
            elif self.sd_config.automate_all:
                self.app_name = self._create_flyio_app()
            else:
                raise plugin_utils.SimpleDeployCommandError(
                    self.sd_config, platform_msgs.no_project_name
                )
        else:
            # More than one undeployed app found. `apps list` doesn't show
            # much specific information for undeployed apps. For exmaple we
            # don't know the creation date, so we can't identify the most
            # recently created app.

            # Rather than a bunch of conditional logic about automate-all runs, just add
            # "Create a new app" for automated runs. If that's chosen, create a new app.
            if self.sd_config.automate_all:
                project_names.append("Create a new app")

            # Show all undeployed apps, ask user to make selection.
            prompt = "\n*** Found multiple undeployed apps on Fly.io. ***"
            for index, name in enumerate(project_names):
                prompt += f"\n  {index}: {name}"
            prompt += "\nWhich app would you like to use? "

            valid_choices = [i for i in range(len(project_names))]

            # Confirm selection, because we do *not* want to deploy
            # against the wrong app.
            confirmed = False
            while not confirmed:
                selection = plugin_utils.get_numbered_choice(
                    self.sd_config, prompt, valid_choices, platform_msgs.no_project_name
                )
                selected_name = project_names[selection]

                confirm_prompt = f"You have selected {selected_name}."
                confirm_prompt += " Is that correct?"
                confirmed = plugin_utils.get_confirmation(
                    self.sd_config, confirm_prompt
                )

            # Create a new app for automated runs, if needed.
            if selected_name == "Create a new app":
                self.app_name = self._create_flyio_app()
            else:
                self.app_name = selected_name

    def _create_flyio_app(self):
        """Create a new Fly.io app.

        Assumes caller already checked for automate_all, and that a suitable app to
        deploy to is not already available.

        Sets:
            str: self.app_name

        Returns:
            str: self.app_name

        Raises:
            SimpleDeployCommandError: if an app can't be created.
        """
        msg = "  Creating a new app on Fly.io..."
        plugin_utils.write_output(self.sd_config, msg)

        cmd = "fly apps create --generate-name --json"
        output_obj = plugin_utils.run_quick_command(self.sd_config, cmd)
        output_str = output_obj.stdout.decode()
        plugin_utils.write_output(self.sd_config, output_str)

        # Get app name.
        app_dict = json.loads(output_str)
        try:
            self.app_name = app_dict["Name"]
        except KeyError:
            raise plugin_utils.SimpleDeployCommandError(
                self.sd_config, platform_msgs.create_app_failed
            )
        else:
            msg = f"  Created new app: {self.app_name}"
            plugin_utils.write_output(self.sd_config, msg)
            return self.app_name

    def _create_db(self):
        """Create a remote database.

        An appropriate db should not already exist. We tell people to create
        an app, and then we take care of everything else. We create a db with
        the name app_name-db.

        We'll look for a db with that name, for example in case someone has already run
        simple_deploy, but only gotten partway through the deployment process. If one
        exists, we'll ask if we should use it. Otherwise, we'll just create a new db for
        the app.

        Sets:
            str: self.db_name

        Returns:
            None

        Raises:
            SimpleDeployCommandError: If can't create a new db, or don't get
            permission to use existing db with matching name.
        """
        msg = "Looking for a Postgres database..."
        plugin_utils.write_output(self.sd_config, msg)

        self.db_name = self.app_name + "-db"
        if self._check_db_exists():
            return self._manage_existing_db()

        # No usable db found. Get region before creating the db.
        self.region = self._get_region()

        # Create a new db.
        msg = f"  Creating a new Postgres database..."
        plugin_utils.write_output(self.sd_config, msg)

        cmd = f"fly postgres create --name {self.db_name} --region {self.region}"
        cmd += " --initial-cluster-size 1 --vm-size shared-cpu-1x --volume-size 1"
        self._confirm_create_db(db_cmd=cmd)

        # Create database. Log command, but don't log output because it should contain
        # db credentials. May want to scrub and then log output.
        plugin_utils.log_info(self.sd_config, cmd)
        plugin_utils.run_slow_command(self.sd_config, cmd, skip_logging=True)

        msg = "  Created Postgres database."
        plugin_utils.write_output(self.sd_config, msg)

        self._attach_db()

    def _get_region(self):
        """Get the region nearest to the user.

        Notes:
        - V1 `fly apps create` automatically configured a region for the app.
        - In V2, an app doesn't have a region; it's really a container for machines,
          which do have regions.
        - We need a region to create a db.
        - `fly postgres create` only prompts for a region, there's no -q or -y.
        - `fly postgres create` does highlight nearest region.
        - `fly platform regions` lists available regions, but doesn't identify nearest.
        - Possible approach:
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
            str: Region with lowest latency for user.
        """

        msg = "Looking for Fly.io region..."
        plugin_utils.write_output(self.sd_config, msg)

        # Get region output.
        url = "https://liveview-counter.fly.dev/"
        r = httpx.get(url, follow_redirects=True)

        re_region = r"Connected to ([a-z]{3})"
        m = re.search(re_region, r.text)
        if m:
            region = m.group(1)

            msg = f"  Found lowest latency region: {region}"
            plugin_utils.write_output(self.sd_config, msg)
        else:
            region = "sea"

            msg = f"  Couldn't find lowest latency region, using 'sea'."
            plugin_utils.write_output(self.sd_config, msg)

        return region

    def _check_db_exists(self):
        """Check if a postgres db already exists that should be used with this app.

        Returns:
            bool: True if appropriate db found; False if not found.
        """

        # First, see if any Postgres clusters exist.
        cmd = "fly postgres list --json"
        output_obj = plugin_utils.run_quick_command(self.sd_config, cmd)
        output_str = output_obj.stdout.decode()
        plugin_utils.log_info(self.sd_config, output_str)

        if "No postgres clusters found" in output_str:
            return False

        # There are some Postgres dbs. Get their names.
        pg_names = [pg_dict["Name"] for pg_dict in json.loads(output_str)]

        # See if any of these names match this app.
        if self.db_name in pg_names:
            msg = f"  Postgres db found: {self.db_name}"
            plugin_utils.write_output(self.sd_config, msg)
            return True
        else:
            msg = "  No matching Postgres database found."
            plugin_utils.write_output(self.sd_config, msg)
            return False

    def _manage_existing_db(self):
        """Figure out what to do with an existing db whose name matches app.

        Returns:
            None: If we can use and configure existing db.

        Raises:
            SimpleDeployCommandError: If we can't use existing db, or fail to configure
            it correctly.
        """
        if self._check_db_attached():
            return self._confirm_use_attached_db()
        else:
            return self._confirm_use_unattached_db()

    def _check_db_attached(self):
        """Check if the db that was found is attached to this app.

        Database is considered attached to this app it has a user with the same
        name as the app, using underscores instead of hyphens. This is the default
        behavior if you create a new app, then a new db, then attach the db to that app.

        Sets:
            list: self.db_users, which can be used in messages to the user.

        Returns:
            bool: True if attached to this app, False if not attached.

        Raises:
            SimpleDeployCommandError: If this db has users in addtion to the default db
            users and a user corresponding to this app, we raise an error.
        """
        # Get users of this db.
        cmd = f"fly postgres users list -a {self.db_name} --json"
        output_obj = plugin_utils.run_quick_command(self.sd_config, cmd)
        output_str = output_obj.stdout.decode()
        plugin_utils.log_info(self.sd_config, output_str)

        pg_users_json = json.loads(output_str)
        self.db_users = [user_dict["Username"] for user_dict in pg_users_json]
        plugin_utils.log_info(self.sd_config, f"DB users: {self.db_users}")

        default_users = {"flypgadmin", "postgres", "repmgr"}
        app_user = self.app_name.replace("-", "_")
        if set(self.db_users) == default_users:
            # This db only has the default users set when a fresh db is made.
            #   Assume it's unattached.
            return False
        elif (app_user in self.db_users) and (len(self.db_users) == 4):
            # This db appears to have been attached to the remote app. Will still need
            # confirmation we can use this db.
            return True
        else:
            # This db has more than the default users, and not just the current app.
            # Let's not touch it. If anyone hits this situation and we should proceed,
            # we'll revisit this block.
            # Note: This path has only been tested once, by manually adding
            # "dummy-user" to the list of db users."
            msg = platform_msgs.cant_use_db(self.db_name, self.db_users)
            raise plugin_utils.SimpleDeployCommandError(self.sd_config, msg)

    def _confirm_use_attached_db(self):
        """Confirm it's okay to use db that's already attached to this app.

        Returns:
            None: If confirmation granted.

        Raises:
            SimpleDeployCommandError: If confirmation denied.
        """
        msg = platform_msgs.use_attached_db(self.db_name, self.db_users)
        plugin_utils.write_output(self.sd_config, msg)

        msg = f"Okay to use {self.db_name} and proceed?"
        if not plugin_utils.get_confirmation(self.sd_config, msg):
            # Permission to use this db denied. Can't simply create a new db,
            # because the name we'd use is already taken.
            raise plugin_utils.SimpleDeployCommandError(
                self.sd_config, platform_msgs.cancel_no_db
            )

    def _confirm_use_unattached_db(self):
        """Confirm it's okay to use db whose name matches this app, but hasn't
        been attached to this app.

        If confirmation given, calls _attach_db().

        Sets:
            str: self.db_name

        Returns:
            None: If confirmation given.

        Raises:
            SimpleDeployCommandError: If confirmation denied.
        """
        msg = platform_msgs.use_unattached_db(self.db_name, self.db_users)
        plugin_utils.write_output(self.sd_config, msg)

        msg = f"Okay to use {self.db_name} and proceed?"
        if plugin_utils.get_confirmation(self.sd_config, msg):
            self._attach_db(self.db_name)
            return
        else:
            # Permission to use this db denied.
            # Can't simply create a new db, because the name we'd use is
            # already taken.
            raise plugin_utils.SimpleDeployCommandError(
                self.sd_config, platform_msgs.cancel_no_db
            )

    def _confirm_create_db(self, db_cmd):
        """Confirm the user wants a database created on their behalf.

        Returns:
            None

        Raises:
            SimpleDeployCommandError: If not confirmed.
        """
        # Ignore this check during testing, and when using --automate-all.
        if self.sd_config.unit_testing or self.sd_config.automate_all:
            return

        # Show the command that will be run on the user's behalf.
        self.stdout.write(platform_msgs.confirm_create_db(db_cmd))
        if plugin_utils.get_confirmation(self.sd_config):
            self.stdout.write("  Creating database...")
        else:
            # Quit and invite the user to create a database manually.
            raise plugin_utils.SimpleDeployCommandError(
                self.sd_config, platform_msgs.cancel_no_db
            )

    def _attach_db(self):
        """Attach the database to the app."""
        msg = "  Attaching database to Fly.io app..."
        plugin_utils.write_output(self.sd_config, msg)
        cmd = f"fly postgres attach --app {self.deployed_project_name} {self.db_name}"

        output_obj = plugin_utils.run_quick_command(self.sd_config, cmd)
        output_str = output_obj.stdout.decode()

        # Show full output, then scrub for logging.
        plugin_utils.write_output(self.sd_config, output_str, skip_logging=True)

        output_scrubbed = [
            l for l in output_str.splitlines() if "DATABASE_URL" not in l
        ]
        output_scrubbed = "\n".join(output_scrubbed)
        plugin_utils.log_info(self.sd_config, output_scrubbed)

        msg = "  Attached database to app."
        plugin_utils.write_output(self.sd_config, msg)
