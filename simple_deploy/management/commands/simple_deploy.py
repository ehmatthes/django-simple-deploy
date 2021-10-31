import sys, os, re, subprocess

from django.core.management.base import BaseCommand, CommandError

from django.conf import settings


class Command(BaseCommand):
    """Perform the initial deployment of a simple project.
    Configure as much as possible automatically.
    """

    def handle(self, *args, **kwargs):
        # DEV: Later, this should check for the platform to deploy to.
        #   Assume deploying to Heroku for now.
        self.stdout.write("Auto-configuring project for deployment to Heroku...")

        self._get_heroku_app_info()
        self._set_heroku_env_var()
        self._inspect_project()
        self._add_simple_deploy_req()
        self._generate_procfile()
        self._add_gunicorn()
        self._check_allowed_hosts()
        self._configure_db()
        self._configure_static_files()
        self._show_success_message()
    

    def _get_heroku_app_info(self):
        """Get info about the Heroku app we're pushing to."""
        # This command assumes the user has already run 'heroku create'.
        #   If they haven't, we'll quit and tell them to.
        #   If they have, we'll get the information we'll need later in the
        #     deployment process.
        #   This is all done through the `heroku apps:info` command.
        #
        #  If they haven't run heroku create, output should go to stderr
        #    and we simply won't have an app name. So, blank app name -> 
        #    tell user to run 'heroku create and then run this command again.
        #  We could consider running this for the user, but we probably want them to 
        #    interact with heroku to some degree.
        #  What happens if they haven't installed Heroku CLI?
        #    Telling them they need to run heroku create probably covers that
        #    for now.

        self.stdout.write("  Inspecting Heroku app...")

        apps_info = subprocess.run(["heroku", "apps:info"], capture_output=True)
        # print('raw apps info:\n', apps_info)

        # Turn stdout info into a list of strings that we can then parse.
        apps_info = apps_info.stdout.decode().split('\n')
        # print('split apps info:\n', apps_info)

        self.heroku_app_name = apps_info[0].removeprefix('=== ')
        self.stdout.write(f"    Found Heroku app: {self.heroku_app_name}")

        if not self.heroku_app_name:
            msg = "\n\nNo Heroku app name has been detected."
            msg += "\n\nThe simple_deploy command assumes you have already run 'heroku create' to start the deployment process. Please run 'heroku create', and then run 'python manage.py simple_deploy' again."
            msg += "\n\nIf you haven't already done so, you will need to install the Heroku CLI: https://devcenter.heroku.com/articles/heroku-cli"

            raise CommandError(msg)

    def _set_heroku_env_var(self):
        """Set a config var to indicate when we're in the Heroku environment.
        This is mostly used to modify settings for the deployed project.
        """
        self.stdout.write("  Setting Heroku environment variable...")
        subprocess.run(["heroku", "config:set", "ON_HEROKU=1"])
        self.stdout.write("    Set ON_HEROKU=1.")
        self.stdout.write("    This is used to define Heroku-specific settings.")

    def _inspect_project(self):
        """Inspect the project, and pull information needed by multiple steps.
        """

         # Get project name. There are a number of ways to get the project
        #   name; for now we'll assume the root url config file has not
        #   been moved from the default location.
        self.project_name = settings.ROOT_URLCONF.removesuffix('.urls')

        self.project_root = settings.BASE_DIR
        self.settings_path = f"{self.project_root}/{self.project_name}/settings.py"

        # Which dependency management approach are we using?
        #   req_txt, pipenv, poetry?
        #   In a simple project, I don't think we should find both Pipfile
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
            subprocess.run(export_cmd_parts)
            self.using_req_txt = True

        # What requirements are already listed?
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

        # Store any heroku-specific settings already in place.
        #   If any have already been written, we don't want to add them again.
        #   This assumes a section at the end, starting with a check for 
        #   'ON_HEROKU' in os.environ.
        with open(self.settings_path) as f:
            settings_lines = f.readlines()

        self.found_heroku_settings = False
        self.current_heroku_settings_lines = []
        for line in settings_lines:
            if "if 'ON_HEROKU' in os.environ:" in line:
                self.found_heroku_settings = True
            if self.found_heroku_settings:
                self.current_heroku_settings_lines.append(line)
        # print(self.current_heroku_settings_lines)

    def _add_simple_deploy_req(self):
        """Add this project to requirements.txt."""
        # Since the simple_deploy app is in INCLUDED_APPS, it needs to be in
        #   requirements.txt. If it's not, Heroku will reject the push.
        self.stdout.write("\n  Looking for django-simple-deploy in requirements...")

        if self.using_req_txt:
            # DEV: This is the correct code once this project is on PyPI.
            #   Also, once this is updated, integration test will need to be updated.
            #   (Substitution for dev branch install address.)
            self._add_req_txt_pkg('django-simple-deploy')
            # self._add_req_txt_pkg('git+git://github.com/ehmatthes/django-simple-deploy')
        elif self.using_pipenv:
            # There's nothing to do here. When you use Pipenv to install something,
            #   it automatically gets added to Pipfile, so simple-deploy should
            #   already be here. There's no separate step like "pip freeze".
            # Modify this later if some people are using a Pipenv approach that
            #   doesn't automatically add installed packages to Pipfile.
            pass

    def _generate_procfile(self):
        """Create Procfile, if none present."""

        #   Procfile should be in project root, if present.
        self.stdout.write(f"\n  Looking in {self.project_root} for Procfile...")
        procfile_present = 'Procfile' in os.listdir(self.project_root)

        if procfile_present:
            self.stdout.write("    Found existing Procfile.")
        else:
            self.stdout.write("    No Procfile found. Generating Procfile...")
            proc_command = f"web: gunicorn {self.project_name}.wsgi --log-file -"

            with open(f"{self.project_root}/Procfile", 'w') as f:
                f.write(proc_command)

            self.stdout.write("    Generated Procfile with following process:")
            self.stdout.write(f"      {proc_command}")


    def _add_gunicorn(self):
        """Add gunicorn to project requirements."""
        self.stdout.write("\n  Looking for gunicorn...")
        
        if self.using_req_txt:
            self._add_req_txt_pkg('gunicorn')
        elif self.using_pipenv:
            # Here.
            self._add_pipenv_pkg('gunicorn')


    def _check_allowed_hosts(self):
        """Make sure project can be served from heroku."""
        # DEV: Still more nesting than I like here, still needs some refactoring.

        self.stdout.write("\n  Making sure project can be served from Heroku...")
        heroku_host = f"{self.heroku_app_name}.herokuapp.com"

        if heroku_host in settings.ALLOWED_HOSTS:
            self.stdout.write(f"    Found {heroku_host} in ALLOWED_HOSTS.")

        elif 'herokuapp.com' in settings.ALLOWED_HOSTS:
            self.stdout.write("    Found 'herokuapp.com' in ALLOWED_HOSTS.")

        elif not settings.ALLOWED_HOSTS:
            # Only add this host if it's not already listed in the heroku-
            #   specific section.
            new_setting = f"ALLOWED_HOSTS.append('{heroku_host}')"
            already_set = self._check_current_heroku_settings(new_setting)

            if not already_set:
                with open(self.settings_path, 'a') as f:
                    self._prep_heroku_setting(f)
                    f.write(f"\n    {new_setting}")

                    self.stdout.write(f"    Added {heroku_host} to ALLOWED_HOSTS for the deployed project.")
            else:
                self.stdout.write(f"    Found {heroku_host} in ALLOWED_HOSTS for the deployed project.")

        else:
            msg = f"\n\nYour ALLOWED_HOSTS setting is not empty, and it does not contain {heroku_host}. ALLOWED_HOSTS is a critical security setting. It is empty by default, which means you or someone else has decided where this project can be hosted."
            msg += "\n\nYour ALLOWED_HOSTS setting currently contains the following entries:"
            msg += f"\n{settings.ALLOWED_HOSTS}"
            msg += f"\n\nWe do not know enough about your project to add to or override this setting. If you want to continue with this deployment, make sure ALLOWED_HOSTS is either empty, or contains the host {heroku_host}."
            msg += "\n\nOnce you have addressed this issue, you can run the simple_deploy command again, and it will pick up where it left off."

            raise CommandError(msg)


    def _configure_db(self):
        """This method is responsible for adding required db-related packages,
        and modifying settings for the Heroku db.
        """
        self.stdout.write("\n  Configuring project for Heroku database...")
        self._add_db_packages()
        self._add_db_settings()


    def _add_db_packages(self):
        """Add packages required for the Heroku db."""
        self.stdout.write("    Adding db-related packages...")

        # psycopg2 2.9 causes "database connection isn't set to UTC" issue.
        #   See: https://github.com/ehmatthes/heroku-buildpack-python/issues/31
        if self.using_req_txt:
            self._add_req_txt_pkg('psycopg2<2.9')
            self._add_req_txt_pkg('dj-database-url')
        elif self.using_pipenv:
            self._add_pipenv_pkg('psycopg2', version="<2.9")
            self._add_pipenv_pkg('dj-database-url')


    def _add_db_settings(self):
        """Add settings for Heroku db."""
        self.stdout.write("   Checking Heroku db settings...")

        # Import dj-database-url.
        # DEV: To refactor this, write a method to take in new setting, msg
        #   if needed to set it, msg if already set.
        new_setting = "import dj_database_url"
        already_set = self._check_current_heroku_settings(new_setting)
        if not already_set:
            with open(self.settings_path, 'a') as f:
                self._prep_heroku_setting(f)
                f.write(f"\n    {new_setting}")
            self.stdout.write("    Added import statement for dj-database-url.")
        else:
            self.stdout.write("    Found import statement for dj-database-url.")

        # Configure db.
        new_setting = "DATABASES = {'default': dj_database_url.config(default='postgres://localhost')}"
        already_set = self._check_current_heroku_settings(new_setting)
        if not already_set:
            with open(self.settings_path, 'a') as f:
                self._prep_heroku_setting(f)
                f.write(f"\n    {new_setting}")
            self.stdout.write("    Added setting to configure Postgres on Heroku.")
        else:
            self.stdout.write("    Found setting to configure Postgres on Heroku.")


    def _configure_static_files(self):
        """Configure static files for Heroku deployment."""

        # Add whitenoise to requirements.
        self.stdout.write("\n  Configuring static files for Heroku deployment...")
        self.stdout.write("    Adding staticfiles-related packages...")
        if self.using_req_txt:
            self._add_req_txt_pkg('whitenoise')
        elif self.using_pipenv:
            self._add_pipenv_pkg('whitenoise')

        # Modify settings.
        # DEV: There are three lines here; this can easily be refactored.
        self.stdout.write("    Configuring static files settings...")

        new_setting = "STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')"
        already_set = self._check_current_heroku_settings(new_setting)
        if not already_set:
            with open(self.settings_path, 'a') as f:
                self._prep_heroku_setting(f)
                f.write(f"\n    {new_setting}")
            self.stdout.write("    Added STATIC_ROOT setting for Heroku.")
        else:
            self.stdout.write("    Found STATIC_ROOT setting for Heroku.")

        new_setting = "STATIC_URL = '/static/'"
        already_set = self._check_current_heroku_settings(new_setting)
        if not already_set:
            with open(self.settings_path, 'a') as f:
                self._prep_heroku_setting(f)
                f.write(f"\n    {new_setting}")
            self.stdout.write("    Added STATIC_URL setting for Heroku.")
        else:
            self.stdout.write("    Found STATIC_URL setting for Heroku.")

        new_setting = "STATICFILES_DIRS = (os.path.join(BASE_DIR, 'static'),)"
        already_set = self._check_current_heroku_settings(new_setting)
        if not already_set:
            with open(self.settings_path, 'a') as f:
                self._prep_heroku_setting(f)
                f.write(f"\n    {new_setting}")
            self.stdout.write("    Added STATICFILES_DIRS setting for Heroku.")
        else:
            self.stdout.write("    Found STATICFILES_DIRS setting for Heroku.")

        # Create folder for static files.
        self.stdout.write("    Checking for static files directory...")
        static_files_dir = f"{self.project_root}/static"
        if os.path.exists(static_files_dir):
            if os.listdir(static_files_dir):
                self.stdout.write("    Found non-empty static files directory.")
            else:
                # Directory exists, but it's empty and won't push to Heroku.
                placeholder_file = f"{static_files_dir}/placeholder.txt"
                with open(placeholder_file, 'w') as f:
                    f.write("This is a placeholder file to make sure this folder is pushed to Heroku.")

                self.stdout.write("    Found empty static files directory; added a placeholder file.")
        else:
            # No static directory exists. Make one, and add a placeholder file.
            os.makedirs(static_files_dir)
            placeholder_file = f"{static_files_dir}/placeholder.txt"
            with open(placeholder_file, 'w') as f:
                f.write("This is a placeholder file to make sure this folder is pushed to Heroku.")

            self.stdout.write("    Created static files directory, and placeholder file.")


    def _show_success_message(self):
        """After a successful run, show a message about what to do next."""
        # DEV: This might be better structured as a block of text in a
        #   separate file, pulled in from this method.
        # Also:
        # - Say something about DEBUG setting.
        #   - Should also consider setting DEBUG = False in the Heroku-specific
        #     settings.
        # - Mention that this script should not need to be run again, unless
        #   creating a new deployment.
        #   - Describe ongoing approach of commit, push, migrate. Lots to consider
        #     when doing this on production app with users, make sure you learn.
        
        msg = "\n\n--- Your project is now configured for deployment on Heroku. ---"
        msg += "\n\nTo deploy your project, you will need to:"
        msg += "\n- Commit the changes made in the configuration process."
        msg += "\n- Push the changes to Heroku."
        msg += "\n- Migrate the database on Heroku."
        msg += "\n\nThe following commands should finish your initial deployment:"
        if self.using_pipenv:
            msg += "\n$ pipenv lock"
        msg += "\n$ git add ."
        msg += '\n$ git commit -am "Configured for Heroku deployment."'
        msg += "\n$ git push heroku main"
        msg += "\n$ heroku run python manage.py migrate"
        msg += "\n\nAfter this, you can see your project by running 'heroku open'."
        msg += f"\nOr, you can visit {self.heroku_app_name}.herokuapp.com."

        self.stdout.write(msg)

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
            self.stdout.write(f"    Found {root_package_name} in requirements file.")
        else:
            with open(self.req_txt_path, 'a') as f:
                # DEV: Align these comments like they're aligned in Pipfile.
                # Align comments, so we don't make req_txt file ugly.
                #   Version specs are in package_name in req_txt approach.
                tab_string = ' ' * (30 - len(package_name))
                f.write(f"\n{package_name}{tab_string}# Added by simple_deploy command.")

            self.stdout.write(f"    Added {package_name} to requirements.txt.")

    def _add_pipenv_pkg(self, package_name, version=""):
        """Add a package to Pipfile, if not already present."""
        pkg_present = any(package_name in r for r in self.requirements)

        if pkg_present:
            self.stdout.write(f"    Found {package_name} in Pipfile.")
        else:
            self._write_pipfile_pkg(package_name, version)


    def _write_pipfile_pkg(self, package_name, version=""):
        """Write package to Pipfile."""
        # Write package name right after [packages].
        #   For simple projects, this shouldn't cause any issues.
        #   If ordering matters, we can address that later.
        with open(self.pipfile_path) as f:
            pipfile_text = f.read()

        if not version:
            version = '*'

        # Don't make ugly comments; make space to align comments.
        #   Align at column 30, so take away name length, and version spec space.
        tab_string = ' ' * (30 - len(package_name) - 5 - len(version))

        new_pkg_string = f'[packages]\n{package_name} = "{version}"{tab_string}# Added by simple_deploy command.'
        pipfile_text = pipfile_text.replace("[packages]", new_pkg_string)

        with open(self.pipfile_path, 'w') as f:
            f.write(pipfile_text)

        self.stdout.write(f"    Added {package_name} to Pipfile.")


    def _check_current_heroku_settings(self, heroku_setting):
        """Check if a setting has already been defined in the heroku-specific
        settings section.
        """
        return any(heroku_setting in line for line in self.current_heroku_settings_lines)

    def _prep_heroku_setting(self, f_settings):
        """Add a block for Heroku-specific settings, if it doesn't already
        exist.
        """

        if not self.found_heroku_settings:
            f_settings.write("\nimport os")
            f_settings.write("\nif 'ON_HEROKU' in os.environ:")

            # Won't need to add these lines anymore.
            self.found_heroku_settings = True