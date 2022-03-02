"""Manages all Azure-specific aspects of the deployment process."""

# Only works with --automate-all flag, because configuration-only approach
#   requires user to do so much manually, that simple_deploy doesn't contribute
#   meaningfully to the deployment process. Leaving the structure in place to 
#   consider configuration-only, if a clear process for that can be outlined.


import sys, os, re, subprocess, random, string, json, time

from django.conf import settings
from django.core.management.base import CommandError

from simple_deploy.management.commands.utils import deploy_messages as d_msgs
from simple_deploy.management.commands.utils import deploy_messages_heroku as dh_msgs
from simple_deploy.management.commands.utils import deploy_messages_azure as da_msgs


class AzureDeployer:
    """Perform the initial deployment of a simple project.
    Configure as much as possible automatically.
    """

    def __init__(self, command):
        """Establishes connection to existing simple_deploy command object."""
        self.sd = command
        self.stdout = self.sd.stdout


    def deploy(self, *args, **options):
        self.stdout.write("Configuring project for deployment to Azure...")

        self._require_automate_all()
        self._confirm_preliminary()

        self._prep_automate_all()
        self._get_azure_settings()
        self.sd._add_simple_deploy_req()

        # While only supporting automate-all, this will be called after we
        #   know the app name.
        # self._check_allowed_hosts()

        self._configure_db()
        self._configure_static_files()
        self._conclude_automate_all()
        self._show_success_message()


    def _require_automate_all(self):
        """Azure deployment requires automate all for now."""
        if not self.sd.automate_all:
            raise CommandError(da_msgs.require_automate_all)


    def _confirm_preliminary(self):
        """Deployment to azure is in a preliminary state, and we need to be
        explicit about that.
        """
        self.stdout.write(da_msgs.confirm_preliminary)

        # Get confirmation.
        confirmed = ''
        while confirmed.lower() not in ('y', 'yes', 'n', 'no'):
            prompt = "\nAre you sure you want to continue deploying to Azure? (yes|no) "
            confirmed = input(prompt)
            if confirmed.lower() not in ('y', 'yes', 'n', 'no'):
                self.stdout.write("  Please answer yes or no.")

        if confirmed.lower() in ('y', 'yes'):
            self.stdout.write("  Continuing with Azure deployment...")
        else:
            # Quit and invite the user to try another platform.
            self.stdout.write(da_msgs.cancel_azure)
            sys.exit()


    def _prep_automate_all(self):
        """Do intial work for automating entire process."""
        # This is platform-specific, because we want to specify exactly what
        #   will be automated.

        # Skip this prep work if --automate-all not used.
        if not self.sd.automate_all:
            return

        # Confirm the user knows exactly what will be automated.
        self.stdout.write(da_msgs.confirm_automate_all)

        # Get confirmation.
        confirmed = ''
        while confirmed.lower() not in ('y', 'yes', 'n', 'no'):
            prompt = "\nAre you sure you want to do this? (yes|no) "
            confirmed = input(prompt)
            if confirmed.lower() not in ('y', 'yes', 'n', 'no'):
                self.stdout.write("  Please answer yes or no.")

        if confirmed.lower() in ('y', 'yes'):
            self.stdout.write("  Continuing with automated deployment...")
        else:
            # Quit and have the user run the command again; don't assume not
            #   wanting to automate means they want to configure.
            self.stdout.write(d_msgs.cancel_automate_all)
            sys.exit()


    def _get_azure_settings(self):
        """Get any azure-specific settings that are already in place.
        """
        # If any azure settings have already been written, we don't want to
        #  add them again. This assumes a section at the end, starting with a
        #  check for 'ON_AZURE' in os.environ.

        with open(self.sd.settings_path) as f:
            settings_lines = f.readlines()

        self.found_azure_settings = False
        self.current_azure_settings_lines = []
        for line in settings_lines:
            if "if 'ON_AZURE' in os.environ:" in line:
                self.found_azure_settings = True
            if self.found_azure_settings:
                self.current_azure_settings_lines.append(line)


    def _check_allowed_hosts(self):
        """Make sure project can be served from azure."""
        # This method is specific to Azure, but the error message is not.
        # This method must be called after we know the app name/ deployed url.

        # DEV: This should be simplified, like the corresponding method in 
        #   deploy_heroku.py. Then, the error message can probably be removed
        #   from deploy_messages.py.

        self.stdout.write("\n  Making sure project can be served from Azure...")

        azure_host = f'{self.app_name}.azurewebsites.net'

        if azure_host in settings.ALLOWED_HOSTS:
            self.stdout.write(f"    Found {azure_host} in ALLOWED_HOSTS.")
        elif '.azurewebsites.net' in settings.ALLOWED_HOSTS:
            # This is a generic entry that allows serving from any Azure URL.
            self.stdout.write("    Found '.azurewebsites.net' in ALLOWED_HOSTS.")
        elif not settings.ALLOWED_HOSTS:
            new_setting = f"ALLOWED_HOSTS.append('{azure_host}')"
            msg_added = f"    Added {azure_host} to ALLOWED_HOSTS for the deployed project."
            msg_already_set = f"    Found {azure_host} in ALLOWED_HOSTS for the deployed project."
            self._add_azure_setting(new_setting, msg_added, msg_already_set)
        else:
            # Let user know there's a nonempty ALLOWED_HOSTS, that doesn't 
            #   contain the current Azure URL.
            msg = d_msgs.allowed_hosts_not_empty_msg(azure_host)
            raise CommandError(msg)


    def _configure_db(self):
        """Add required db-related packages, and modify settings for Postgres db.
        """
        self.stdout.write("\n  Configuring project for Azure Postgres database...")
        self._add_db_packages()
        self._add_db_settings()


    def _add_db_packages(self):
        """Add packages required for the Azure Postgres db."""
        self.stdout.write("    Adding db-related packages...")

        # psycopg2 2.9 causes "database connection isn't set to UTC" issue.
        #   See: https://github.com/ehmatthes/heroku-buildpack-python/issues/31
        # Note: I don't think the 2.9 issue is a problem on Azure, from separate
        #   testing. I'll remove this note after it's clear that 2.9 is okay,
        #   and we'll probably use psycopg3 anyway.
        if self.sd.using_req_txt:
            self.sd._add_req_txt_pkg('psycopg2<2.9')
        elif self.sd.using_pipenv:
            self.sd._add_pipenv_pkg('psycopg2', version="<2.9")


    def _add_db_settings(self):
        """Add settings for Azure db."""
        self.stdout.write("   Checking Azure db settings...")

        # Configure db.
        # DEV: This is written as one line, to keep _get_azure_settings() working
        #   as it's currently written. Rewrite this as a block, and update get settings()
        #   to work with multiline settings.
        new_setting = "DATABASES = {'default': {'ENGINE': 'django.db.backends.postgresql', 'NAME': os.environ['DBNAME'], 'HOST': os.environ['DBHOST'] + '.postgres.database.azure.com', 'USER': os.environ['DBUSER'] + '@' + os.environ['DBHOST'], 'PASSWORD': os.environ['DBPASS']}}"
        msg_added = "    Added setting to configure Postgres on Azure."
        msg_already_set = "    Found setting to configure Postgres on Azure."
        self._add_azure_setting(new_setting, msg_added, msg_already_set)


    def _configure_static_files(self):
        """Configure static files for Azure deployment."""

        self.stdout.write("\n  Configuring static files for Azure deployment...")

        # Add whitenoise to requirements.
        self.stdout.write("    Adding staticfiles-related packages...")
        if self.sd.using_req_txt:
            self.sd._add_req_txt_pkg('whitenoise')
        elif self.sd.using_pipenv:
            self.sd._add_pipenv_pkg('whitenoise')

        # Modify settings, and add a directory for static files.
        self._add_static_file_settings()


    def _add_static_file_settings(self):
        """Add all settings needed to manage static files."""
        self.stdout.write("    Configuring static files settings...")

        new_setting = "MIDDLEWARE.insert(1, 'whitenoise.middleware.WhiteNoiseMiddleware')"
        msg_added = "    Added whitenoise to MIDDLEWARE."
        msg_already_set = "    Found whitenoise in MIDDLEWARE."
        self._add_azure_setting(new_setting, msg_added, msg_already_set)

        new_setting = "STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'"
        msg_added = "    Added STATICFILES_STORAGE setting for Azure."
        msg_already_set = "    Found STATICFILES_STORAGE setting for Azure."
        self._add_azure_setting(new_setting, msg_added, msg_already_set)

        new_setting = "STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')"
        msg_added = "    Added STATIC_ROOT setting for Azure."
        msg_already_set = "    Found STATIC_ROOT setting for Azure."
        self._add_azure_setting(new_setting, msg_added, msg_already_set)


    def _conclude_automate_all(self):
        """Finish automating the push to Azure."""

        # All az cli commands are issued here, after the project has been
        #   configured.
        if not self.sd.automate_all:
            return

        self.stdout.write("  Pushing to Azure...")

        # Parameters for Azure deployment.
        location = 'westus2'
        db_sku = 'B_Gen5_1'

        self._add_migration_script()
        self._install_dbup()
        self._create_azure_group(location)
        self._create_azure_plan()
        unique_string = self._create_azure_app_name()

        # Now that we have an app name, modify ALLOWED_HOSTS.
        self._check_allowed_hosts()

        self._commit_changes()
        self._create_azure_db(location, db_sku, unique_string)
        self._pause(30)
        creation_output = self._create_azure_app()
        self._parse_creation_output(creation_output)
        self._set_post_deploy_script()
        self._set_azure_env_vars()
        self._pause(30)
        self._set_git_remote()
        self._push_azure()        
        self._pause(30)
        self._open_azure_app()


    def _show_success_message(self):
        """After a successful run, show a message about what to do next."""

        # DEV:
        # - Say something about DEBUG setting.
        #   - Should also consider setting DEBUG = False in the Azure-specific
        #     settings.
        # - Mention that this script should not need to be run again, unless
        #   creating a new deployment.
        #   - Describe ongoing approach of commit, push, migrate. Lots to consider
        #     when doing this on production app with users, make sure you learn.

        if self.sd.automate_all:
            # Show how to make future deployments.
            # DEV: Replace this with actual project name:
            msg = da_msgs.success_msg_automate_all(self.app_name,
                    self.current_branch)
        else:
            # Show steps to finish the deployment process.
            # DEV: This block should not be reached until we support a
            #   configuration-only approach for Azure.
            msg = da_msgs.success_msg(self.sd.using_pipenv, self.app_name)

        self.stdout.write(msg)


    # --- Utility methods ---

    def _check_current_azure_settings(self, azure_setting):
        """Check if a setting has already been defined in the azure-specific
        settings section.
        """
        return any(azure_setting in line for line in self.current_azure_settings_lines)


    def _add_azure_setting(self, new_setting, msg_added='',
            msg_already_set=''):
        """Add a new setting to the azure-specific settings, if not already
        present.
        """
        already_set = self._check_current_azure_settings(new_setting)
        if not already_set:
            with open(self.sd.settings_path, 'a') as f:
                self._prep_azure_setting(f)
                f.write(f"\n    {new_setting}")
                self.stdout.write(msg_added)
        else:
            self.stdout.write(msg_already_set)


    def _prep_azure_setting(self, f_settings):
        """Add a block for Azure-specific settings, if it doesn't already
        exist.
        """
        if not self.found_azure_settings:
            # DEV: Should check if `import os` already exists in settings file.
            f_settings.write("\nimport os")
            f_settings.write("\nif 'ON_AZURE' in os.environ:")

            # Won't need to add these lines anymore.
            self.found_azure_settings = True


    def _add_migration_script(self):
        """Add a migration script, since we'll be handling the initial
        migration.
        """
        self.stdout.write("  Adding script to run initial migration...")
        run_migration_file = f'{self.sd.project_root}/run_azure_migration.sh'
        with open(run_migration_file, 'w') as f:
            f.write('python manage.py migrate\n')


    def _install_dbup(self):
        """Make sure user has Azure db-up extension installed."""
        self.stdout.write("  Adding db-up to Azure CLI...")
        cmd_str = "az extension add --name db-up"
        cmd_parts = cmd_str.split(' ')
        subprocess.run(cmd_parts)
        self.stdout.write("    Added db-up.")


    def _create_azure_group(self, location):
        """Create a group with a location that works for free plans."""
        self.stdout.write("  Creating group...")
        cmd_str = f"az group create --location {location} --name SimpleDeployGroup"
        cmd_parts = cmd_str.split(' ')
        subprocess.run(cmd_parts)
        self.stdout.write("    Created group.")


    def _create_azure_plan(self):
        """Create a plan on the specified tier."""
        self.stdout.write(f"\n  Creating Azure {self.sd.azure_plan_sku} plan...")
        # Note: I keep getting "error in sideband demultiplexer" errors. I think it's because
        #   I'm using the free tier too often. Try paid plans.
        cmd_str = f"az appservice plan create --resource-group SimpleDeployGroup --name SimpleDeployPlan --sku {self.sd.azure_plan_sku} --is-linux"
        cmd_parts = cmd_str.split(' ')
        subprocess.run(cmd_parts)
        self.stdout.write("    Created plan.")


    def _create_azure_app_name(self):
        """Create a unique app name for deployment.
        """
        self.stdout.write("\n  Creating app name...")
        unique_string = ''.join(random.choices(string.ascii_letters + string.digits, k=16))
        project_name_slug = self.sd.project_name.replace('_', '-')
        self.app_name = f"{project_name_slug}-{unique_string}"
        self.stdout.write(f"    Created name: {self.app_name}")

        # This same unique string will be used to create db as well.
        return unique_string


    def _commit_changes(self):
        """Commit changes in preparation for push to Azure server."""
        self.stdout.write("  Committing changes before deployment...")
        self.stdout.write("    Adding changes...")
        subprocess.run(['git', 'add', '.'])
        self.stdout.write("    Committing changes...")
        subprocess.run(['git', 'commit', '-am', '"Configured project for deployment."'])


    def _create_azure_db(self, location, db_sku, unique_string):
        """Create an Azure Postgres database."""
        # Note that this is significantly more expensive than what many 
        #   people may want for their first deployment. This should be
        #   communicated, even though it's a user's responsibility to know
        #   what costs they are incurring.

        self.stdout.write("  Creating Postgres database...")

        self.db_server_name = f"sd-pg-server-{unique_string}"
        self.db_name = f"sd-db-{unique_string}"
        self.db_user = f"sd_db_admin_{unique_string}"
        # Ensure db password has appropriate complexity, and is entirely distinct from other credentials.
        self.db_password = ''.join(random.choices(string.ascii_letters + string.digits + '!@#$%^&*', k=32))

        self.stdout.write(f"    DB server name: {self.db_server_name}")
        self.stdout.write(f"    DB name: {self.db_name}")
        self.stdout.write(f"    DB user: {self.db_user}")
        self.stdout.write(f"    DB password: {self.db_password}")

        cmd_str = f"az postgres up --resource-group SimpleDeployGroup --location {location} --sku-name {db_sku} --server-name {self.db_server_name} --database-name {self.db_name} --admin-user {self.db_user} --admin-password {self.db_password}"
        cmd_parts = cmd_str.split(' ')
        subprocess.run(cmd_parts)
        self.stdout.write("    Created Postgres database...")


    def _pause(self, pause_length):
        """Sometimes need to pause a moment after creating a resource."""
        self.stdout.write(f"  Sleeping {pause_length}s after building resource...")
        time.sleep(pause_length)

        # DEV: How make this loop work with stdout.write()?
        # print('-'*60)
        # for _ in range(60):
        #     time.sleep(1)
        #     print('.', end='')

        self.stdout.write('\n    Finished sleeping.')


    def _create_azure_app(self):
        """Create an Azure appservice app."""
        self.stdout.write("  Creating app...")
        cmd_str = f"az webapp create --resource-group SimpleDeployGroup --plan SimpleDeployPlan --name {self.app_name} --runtime PYTHON:3.8 --deployment-local-git"
        cmd_parts = cmd_str.split(' ')
        output = subprocess.run(cmd_parts, capture_output=True)
        self.stdout.write("    Created app.")

        return output


    def _parse_creation_output(self, output):
        """Parse output from creating app.
        Looking for publishing credentials.
        """

        # DEV: This method can certainly be refactored.
        #   Either break it into smaller pieces and call from here, or
        #   call specific steps from _conclude_automate_all().

        self.stdout.write("  Parsing output...")
        output_str = output.stdout.decode()
        create_output_str = output_str
        # DEV: This is used by testing script test_azure_deployment.sh.
        #   Should probably replace this with just the information that the
        #   testing script needs, which would simplify that script as well.
        self.stdout.write(output_str)

        # DEV: I don't think this is currently being used.
        output_str = output_str.replace('null', '""')
        output_str = output_str.replace('\\', '\\\\')
        create_output_dict = json.loads(output_str)
        self.stdout.write("    Parsed output from create command.")

        # Get credentials for pushing the repository.
        self.stdout.write("    Getting publish credentials...")
        cmd_str = f"az webapp deployment list-publishing-profiles --resource-group SimpleDeployGroup --name {self.app_name}"
        cmd_parts = cmd_str.split(' ')
        output = subprocess.run(cmd_parts, capture_output=True)
        output_str = output.stdout.decode()
        self.stdout.write(output_str)
        publish_output_list = json.loads(output_str)

        # Get username, password, and build correct git uri.
        username = publish_output_list[0]['userName']
        password = publish_output_list[0]['userPWD']
        self.stdout.write(f"      username: {username}")
        self.stdout.write(f"      password: {password}")

        # DEV: Rather than running this re against entire output string, run it against
        #   the deploymentLocalGitUrl pulled from the output json dict.
        self.stdout.write("    Building git url and push command...")
        re_git_url = r'"deploymentLocalGitUrl": "https://(.*)@(.*).scm.azurewebsites.net/(.*).git",'
        m = re.search(re_git_url, create_output_str)

        # Get the current branch name. Get the first line of status output,
        #   and keep everything after "On branch ".
        git_status = subprocess.run(['git', 'status'], capture_output=True, text=True)
        self.current_branch = git_status.stdout.split('\n')[0][10:]

        self.git_url = f'https://{username}:{password}@{m.group(2).lower()}.scm.azurewebsites.net:443/{m.group(3).lower()}.git'
        self.push_command = f"git push {self.git_url} {self.current_branch}:master"

        self.stdout.write(f'    git url: {self.git_url}')
        self.stdout.write(f'    push command: {self.push_command}')
        self.stdout.write("    Built git url and push command.")


    def _set_post_deploy_script(self):
        """Set post-deploy script, which currently only runs initial
        migration.
        """
        self.stdout.write("  Setting post-deploy script...")
        cmd_str = f"az webapp config appsettings set --resource-group SimpleDeployGroup --name {self.app_name} --settings POST_BUILD_COMMAND=run_azure_migration.sh"
        cmd_parts = cmd_str.split(' ')
        subprocess.run(cmd_parts)
        self.stdout.write("    Set post-deploy script.")


    def _set_azure_env_vars(self):
        """Set all environment variables that Azure will need."""

        # Set ON_AZURE app setting.
        self.stdout.write("  Setting ON_AZURE...")
        cmd_str = f"az webapp config appsettings set --resource-group SimpleDeployGroup --name {self.app_name} --settings ON_AZURE=1"
        cmd_parts = cmd_str.split(' ')
        subprocess.run(cmd_parts)
        self.stdout.write("    Set ON_AZURE.")

        self.stdout.write("  Setting env vars for db connection...")
        cmd_str = f"az webapp config appsettings set --resource-group SimpleDeployGroup --name {self.app_name} --settings DBHOST={self.db_server_name}"
        cmd_parts = cmd_str.split(' ')
        subprocess.run(cmd_parts)

        cmd_str = f"az webapp config appsettings set --resource-group SimpleDeployGroup --name {self.app_name} --settings DBNAME={self.db_name}"
        cmd_parts = cmd_str.split(' ')
        subprocess.run(cmd_parts)

        cmd_str = f"az webapp config appsettings set --resource-group SimpleDeployGroup --name {self.app_name} --settings DBUSER={self.db_user}"
        cmd_parts = cmd_str.split(' ')
        subprocess.run(cmd_parts)

        cmd_str = f"az webapp config appsettings set --resource-group SimpleDeployGroup --name {self.app_name} --settings DBPASS={self.db_password}"
        cmd_parts = cmd_str.split(' ')
        subprocess.run(cmd_parts)
        self.stdout.write("    Set env vars for db.")


    def _set_git_remote(self):
        """Add a git remote address for azure."""
        self.stdout.write("  Setting git remote...")
        cmd_str = f"git remote add azure {self.git_url}"
        cmd_parts = cmd_str.split(' ')
        subprocess.run(cmd_parts)
        self.stdout.write("    Set git remote.")


    def _push_azure(self):
        """Push project to azure."""
        # We need to use the push command constructed earlier, which has
        #   credentials in it. If we call a simple
        #   `git push azure main:master`, the script will pause and ask
        #   for a username/ password.
        self.stdout.write("  Pushing to remote...")
        cmd_str = self.push_command
        cmd_parts = cmd_str.split(' ')
        subprocess.run(cmd_parts)
        self.stdout.write("    Pushed to remote.")


    def _open_azure_app(self):
        """Open newly-deployed app in browser."""
        self.stdout.write("  Opening in browser...")
        cmd_str = f"az webapp browse --resource-group SimpleDeployGroup --name {self.app_name}"
        cmd_parts = cmd_str.split(' ')
        subprocess.run(cmd_parts)
        self.stdout.write("    Opened in browser.")