# Test the simple_deploy process for deployment on Heroku.

# This tests the latest push on the current branch.
#   It does NOT test the local version of the code.
#   This is because Heroku needs to install the code for the full integration
#   test to work, and Heroku can't install code directly from a local machine.

# Overall approach:
# - Create a temporary working location, outside of any existing git repo.
# - Clone the test instance of the LL project.
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
# Test the latest pushed version of the current branch:
#   $ ./integration_tests/autoconfigure_deploy_test.sh
#
# Test the most recent PyPI release:
#   $ ./integration_tests/autoconfigure_deploy_test.sh test_pypi_release


# --- Get options for current test run. --
# t: Target for testing.
#    current_branch, pypi
# d: Dependency management approach that's being tested.
#    req_txt, pipenv, poetry
# o: Options for the simple_deploy run.
#    automate_all
# p: Platform to push to.
#    heroku, azure
#
# DEV: Not sure if formatting of this is standard.
# Usage:
#  $ ./autconfigure_deploy_test.sh -t [pypi, current_branch] -d [req_txt|pipenv|poetry] -p [heroku|azure]


# --- Get CLI arguments. ---

target="current_branch"
dep_man_approach="req_txt"
platform="heroku"

# Options:
# - test_automate_all
cli_sd_options=""

while getopts t:d:o:p flag
do
    case "${flag}" in
        t) target=${OPTARG};;
        d) dep_man_approach=${OPTARG};;
        o) cli_sd_options=${OPTARG};;
        p) platform=${OPTARG};;
    esac
done

# --- Make sure user is okay with building a temp environment in $HOME. ---
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

# Only one possibility for cli_sd_options right now.
if [ "$cli_sd_options" = 'automate_all' ]; then
    test_automate_all=true
fi

# Get current branch and remote Git address, so we know which version 
#   of the app to test against.
echo "\nExamining current branch..."
current_branch=$(git status | head -n 1)
current_branch=${current_branch:10}
echo "  Current branch: $current_branch"

if [ "$target" = pypi ]; then
    # Install address is just the package name, which will be pulled from PyPI.
    # Note: I believe this is just for req_txt approach.
    install_address="django-simple-deploy"
else
    # Install address is the git remote address with the current branch name.
    remote_address=$(git remote get-url origin)
    install_address="git+$remote_address@$current_branch"

    # Pipenv also needs something about the egg:
    if [ "$dep_man_approach" = 'pipenv' ]; then
        install_address="$install_address#egg=django-simple-deploy"
    fi
fi

echo "  Installing from: $install_address"

# Make tmp location and clone LL test repo.
echo "\nBuilding temp environment and cloning LL project:"

script_dir=$(pwd)
tmp_dir="$HOME/tmp_django_simple_deploy_test"
mkdir "$tmp_dir"
echo "  Made temporary directory: $tmp_dir"

echo "  Cloning LL project into tmp directory..."
# The cloned repository has several versions of the test project.
#   All testing options work with this same repository.
git clone  https://github.com/ehmatthes/learning_log_heroku_test.git $tmp_dir

# Need a Python environment for configuring the test Django project.
# This environment might need to be deactivated before running the Python testing
#   script below.
echo "  Building Python environment..."

# cd'ing into the version of the project we're testing.
#   We also get rid of the git repository from cloning, so we can use git on just
#   the version of the project we're testing.
cd "$tmp_dir/"
rm -rf .git/

if [ "$dep_man_approach" = 'req_txt' ]; then
    cd "req_txt_unpinned"
    python3 -m venv ll_env
    source ll_env/bin/activate
    pip install --upgrade pip
    pip install -r requirements.txt
    # We may have installed from unpinned dependencies, so pin them now for Heroku.
    pip freeze > requirements.txt
elif [ "$dep_man_approach" = 'pipenv' ]; then
    # This test usually runs inside a venv for the overall django-simple-deploy
    #   project. Pipenv will install to that environment unless we create a venv
    #   for it to use.
    cd "pipenv_unpinned"

    python3 -m venv ll_env
    source ll_env/bin/activate

    pip install --upgrade pip
    pip install pipenv
    # We'll only lock once, just before committing for deployment.
    python3 -m pipenv install --skip-lock
elif [ "$dep_man_approach" = 'poetry' ]; then
    cd "poetry_unpinned"

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
    #   (It was failing when run after creating ll_env, maybe it works better
    #   before making the new venv?)
    yes | $poetry_cmd cache clear --all pypi

    # Make a new venv in this tmp project directory, so Poetry will use it,
    #   and we can destroy it at the end of testing.
    python3 -m venv ll_env
    source ll_env/bin/activate

    $poetry_cmd install

    echo "--- info ---"
    $poetry_cmd env info
fi

echo "  Initializing Git repostitory..."
git init
git add .
git commit -am "Initial commit."

# Now install django-simple-deploy, just as a user would.
#   Except, we'll install the version from the current branch.
if [ "$dep_man_approach" = 'req_txt' ]; then
    echo "  Installing django-simple-deploy..."
    pip install $install_address
elif [ "$dep_man_approach" = 'pipenv' ]; then
    python3 -m pipenv install $install_address --skip-lock
elif [ "$dep_man_approach" = 'poetry' ]; then
    $poetry_cmd add $install_address
fi

echo "\nAdding simple_deploy to INSTALLED_APPS..."
sed -i "" "s/# Third party apps./# Third party apps.\n    'simple_deploy',/" learning_log/settings.py


# --- Test platform-specific deployment processes. ---

# Source each platform-specific file, so it has access to all current variables.
#   Bash note: Simply calling the script runs it in a subshell, without
#   access to any variables defined in the calling script.

if [ "$platform" = 'heroku' ]; then
    source $script_dir/integration_tests/test_heroku_deployment.sh
elif [ "$platform" = 'azure' ]; then
    source $script_dir/integration_tests/test_azure_deployment.sh
else
    echo "  That platform is not supported."
fi