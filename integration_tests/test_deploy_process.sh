# Test the simple_deploy process for deployment on Heroku.

# Overall approach:
# - Create a temporary working location, outside of any existing git repo.
# - Copy the sample project to the tmp directory.
# - Build a Python venv.
# - Follow the deploy steps.
# - Run automated availability and functionality tests.
#   - This could be a call to a .py file
# - Prompt for whether to destroy deployed app (default yes).
#   At this time, user can also use the deployed app.
# - Destroy temp project.
# - Destroy heroku app.

# Usage
#
# Test the current local version of the project:
#   $ ./integration_tests/test_deploy_process.sh
#
# Test the most recent PyPI release:
#   $ ./integration_tests/test_deploy_process.sh -t pypi


# --- Get options for current test run. --
# t: Target for testing.
#    development_version, pypi
# d: Dependency management approach that's being tested.
#    req_txt, poetry, pipenv
# p: Platform to push to.
#    heroku, _____
# o: Options for the simple_deploy run.
#    automate_all

#
# DEV: Not sure if formatting of this is standard.
# Usage:
#  $ ./test_deploy_process.sh -t [pypi, development_version] -d [req_txt|poetry|pipenv] -p [heroku]


# --- Process CLI arguments. ---

target="development_version"
dep_man_approach="req_txt"
platform=""

# Options:
# - test_automate_all
cli_sd_options=""

while getopts t:d:o:p: flag
do
    case "${flag}" in
        t) target=${OPTARG};;
        d) dep_man_approach=${OPTARG};;
        o) cli_sd_options=${OPTARG};;
        p) platform=${OPTARG};;
    esac
done

# Require the platform (-p) flag.
if [ "$platform" = "" ]; then
    echo "\nA target platform for integration testing must be specified."
    echo "  Test a Heroku deployment: $ ./integration_tests/test_deploy_process.sh -p heroku"
    echo "  Test a Platform.sh deployment: $ ./integration_tests/test_deploy_process.sh -p platform_sh\n"
    exit 1
fi

# Make sure platform is one of the currently-supported platforms.
#   (My bash is not the strongest, feel free to suggest a better logical test.)
if [[ "$platform" != "heroku" ]] && [[ "$platform" != "platform_sh" ]]; then
    echo "\nIntegration testing does not support the platform you have specified: $platform"
    echo "  Only the following platforms are supported: heroku, platform_sh\n"
    exit 1
fi

# Only one possibility for cli_sd_options right now.
if [ "$cli_sd_options" = 'automate_all' ]; then
    test_automate_all=true
fi

# --- Copy sample project to tmp location in $HOME and build testing venv. ---

# Make sure user is okay with building a temp environment in $HOME.
echo ""
echo "This test will build a temporary directory in your home folder."
echo "  It will also create an app on your account for the selected platform."

while true; do
    read -p "Proceed? " yn
    case $yn in 
        [Yy]* ) echo "\nOkay, proceeding with tests..."; break;;
        [Nn]* ) echo "\nOkay, not running tests."; exit;;
        * ) echo "Please answer yes or no.";;
    esac
done

# Make tmp location and copy sample project.
echo "\nBuilding temp environment and copying sample project:"

script_dir=$(pwd)
tmp_dir="$HOME/tmp_django_simple_deploy_test"
mkdir "$tmp_dir"
echo "  Made temporary directory: $tmp_dir"
echo "  copying sample project into tmp directory..."
# Reminder: trailing slash on source dir copies contents, without making parent folder
#   in destination directory.
rsync -ar sample_project/blog_project/ $tmp_dir

# Need a Python environment for configuring the test Django project.
# This environment might need to be deactivated before running the Python testing
#   script below.
echo "  Building Python environment..."

# cd'ing into the version of the project we're testing.
cd "$tmp_dir/"

if [ "$dep_man_approach" = 'req_txt' ]; then
    # Remove other dependency files.
    rm Pipfile
    rm pyproject.toml

    python3 -m venv b_env
    source b_env/bin/activate
    pip install --upgrade pip
    pip install -r requirements.txt
    # We may have installed from unpinned dependencies, so pin them now for Heroku.
    pip freeze > requirements.txt
elif [ "$dep_man_approach" = 'pipenv' ]; then
    # This test usually runs inside a venv for the overall django-simple-deploy
    #   project. Pipenv will install to that environment unless we create a venv
    #   for it to use.

    # Remove other dependency files.
    rm requirements.txt
    rm pyproject.toml

    python3 -m venv b_env
    source b_env/bin/activate

    pip install --upgrade pip
    pip install pipenv
    # We'll only lock once, just before committing for deployment.
    pipenv install --skip-lock
elif [ "$dep_man_approach" = 'poetry' ]; then
    # Remove other dependency files.
    rm requirements.txt
    rm Pipfile

    poetry_cmd="/Users/eric/Library/Python/3.10/bin/poetry"

    # DEV: Poetry cache issues have been really hard to troubleshoot. At one point
    #   testing against pypi code that doesn't even recognize poetry projects
    #   was passing. The only explanation was it was using local code, even
    #   though it reported what looked like pypi code. So, clear cache before
    #   each test run. Also many poetry installation steps fail without clearing
    #   cache manually first. 
    # Leaving attempted cache clearing approaches commented here until
    #   this issue is clearly resolved.
    # If you have issues testing poetry, run the command
    #   `poetry cache clear --all pypi` manually before running the test.
    #
    # See: https://github.com/python-poetry/poetry/issues/521
    # and: https://github.com/python-poetry/poetry/issues/949
    # 
    # This approach fails, because --no-interaction accepts default answer,
    #   which is 'no'.
    # $poetry_cmd cache clear --all pypi --no-interaction
    #
    # This should pipe 'y' to the command, but it doesn't seem to work.
    #   (It was failing when run after creating b_env, maybe it works better
    #   before making the new venv?)
    yes | $poetry_cmd cache clear --all pypi

    # Make a new venv in this tmp project directory, so Poetry will use it,
    #   and we can destroy it at the end of testing.
    python3 -m venv b_env
    source b_env/bin/activate

    $poetry_cmd install

    echo "--- info ---"
    $poetry_cmd env info
fi

echo "  Initializing Git repostitory..."
git init
git add .
git commit -am "Initial commit."


# --- Use django-simple-deploy as a user would. ---

# Now install django-simple-deploy, just as a user would.
# - Install local dev version by default.
# - If test targets pypi, install from there.
echo "  Installing django-simple-deploy..."

# Define $dependency_string for based on whether we're testing the local 
#   development version or the pypi version.
if [ "$target" = pypi ]; then
    # Dependency string is just the package name.
    dependency_string="django-simple-deploy"
else
    # Install from the local directory.
    dependency_string="$script_dir"
fi

if [ "$dep_man_approach" = 'req_txt' ]; then
    pip install $dependency_string
elif [ "$dep_man_approach" = 'pipenv' ]; then
    pipenv install $dependency_string --skip-lock
    # When users install from pypi, their Pipfile works on the remote platform.
    # This Pipfile will not, because it now has a local path for django-simple-deploy.
    # Remove the local path from Pipfile: django-simple-deploy = {path = "$script_dir"} and replace with "*"
    # DEV: This is my awkward-but-works bash way to bring double quotes and variable values into a sed re.
    #   This can probably be collapsed into one sed line.
    version_spec='"*"'
    script_dir_str='"'
    script_dir_str+=$script_dir
    script_dir_str+='"'
    sed -i "" "s#django-simple-deploy = {path = $script_dir_str}#django-simple-deploy = $version_spec#" Pipfile
elif [ "$dep_man_approach" = 'poetry' ]; then
    # Poetry throws an error if I try to install from a local directory using this command:
    # $poetry_cmd add $dependency_string
    # So, workaround since we only need the development version installed locally, not on Heroku:
    #   Use pip to install the appropriate version here, just like in the req_txt block.
    #   Then manually add django-simple-deploy to pyproject.toml, so the remote version
    #   will just install from pypi.
    pip install $dependency_string
    version_spec='"*"'
    sed -i "" "s#requests#django-simple-deploy = $version_spec\nrequests#" pyproject.toml
fi

# Clean up build/ dir that pip leaves behind.
rm -rf "$script_dir/build/"
rm -rf "$script_dir/django_simple_deploy.egg-info/"

echo "\nAdding simple_deploy to INSTALLED_APPS..."
sed -i "" "s/# Third party apps./# Third party apps.\n    'simple_deploy',/" blog/settings.py


# --- Test platform-specific deployment processes. ---

# Source each platform-specific file, so it has access to all current variables.
#   Bash note: Simply calling the script runs it in a subshell, without
#   access to any variables defined in the calling script.

if [ "$platform" = 'heroku' ]; then
    source $script_dir/integration_tests/test_heroku_deployment.sh
elif [ "$platform" = 'platform_sh' ]; then
    source $script_dir/integration_tests/test_platformsh_deployment.sh
fi