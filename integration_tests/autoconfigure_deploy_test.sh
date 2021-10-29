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
#
# DEV: Not sure if fromatting of this is standard.
# Usage:
#  $ ./autconfigure_deploy_test.sh -t [pypi, current_branch] -d [req_txt|pipenv|poetry]

target="current_branch"
dep_man_approach="req_txt"
while getopts t:d: flag
do
    case "${flag}" in
        t) target=${OPTARG};;
        d) dep_man_approach=${OPTARG};;
    esac
done

# --- Make sure user is okay with building a temp environment in $HOME. ---
echo ""
echo "This test will build a temporary directory in your home folder."
echo "  It will also create a heroku app on your account."
echo "  (By calling 'heroku create', which you'll need to authorize.)"
while true; do
    read -p "Proceed? " yn
    case $yn in 
        [Yy]* ) echo "\nOkay, proceeding with tests..."; break;;
        [Nn]* ) echo "\nOkay, not running tests."; exit;;
        * ) echo "Please answer yes or no.";;
    esac
done

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

# cd'ing into the version of the project with unpinned dependencies.
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
fi

echo "\nAdding simple_deploy to INSTALLED_APPS..."
sed -i "" "s/# Third party apps./# Third party apps.\n    'simple_deploy',/" learning_log/settings.py

echo "Running heroku create..."
heroku create

echo "Running manage.py simple_deploy..."
python manage.py simple_deploy

# After running simple_deploy, need to regenerate the lock file.
if [ "$dep_man_approach" = 'pipenv' ]; then
    python3 -m pipenv lock
fi

# Heroku needs a copy of requirements with the same django-simple-deploy
#   we're testing against. Modify django-simple-deploy to match install_address.
#   This is important to verify, so we'll routinely include it in the test output.
#   This is only needed if we're testing against a GitHub repo.
if [ "$target" = 'current_branch' ]; then
    if [ "$dep_man_approach" = 'req_txt' ]; then
        echo "\nOriginal requirements.txt; should see django-simple-deploy:"
        cat requirements.txt

        echo "  Modifying requirements.txt to require the current branch version on Heroku..."
        sed -i "" "s|django-simple-deploy|$install_address|" requirements.txt

        echo "\nModified requirements.txt; should see django-simple-deploy address you're trying to test:"
        cat requirements.txt
    elif [ "$dep_man_approach" = 'pipenv' ]; then
        # No need for this; installing from branch with Pipenv specifies this location
        #   in Pipfile. :)
        echo "No need to modify Pipfile."

        # echo '\nOriginal Pipfile; should see django-simple-deploy = "*":'
        # cat Pipfile

        # echo "  Modifying Pipfile to require the current branch version on Heroku..."
        # sed -i "" "s|django-simple-deploy = \"*\"|django-simple-deploy = {ref = \"$current_branch\", git = \"https://github.com/ehmatthes/django-simple-deploy.git\"}"

        # echo "\nModified Pipfile; should see django-simple-deploy address you're trying to test:"
        # cat Pipfile
    fi
fi

echo "\n\nCommitting changes..."
git add .
git commit -am "Configured for deployment."

echo "Pushing to heroku..."
# DEV: There should probably be a variable to track which branch we're using on the test repository.
# git push heroku main
git push heroku main
heroku run python manage.py migrate
heroku open

app_name=$(heroku apps:info | grep "===")
app_name=${app_name:4}
echo "  Heroku app name: $app_name"

app_url=$(heroku apps:info | grep "Web URL")
app_url=${app_url:16}
echo "  Heroku URL: $app_url"

# Call Python script for functional testing of app.
#   May want to prompt for this.
echo "\n  Testing functionality of deployed app..."

# Need requests to run functionality tests.
#   This uses the same venv that was built for deploying the project.
if [ "$dep_man_approach" = 'req_txt' ]; then
    pip install requests
elif [ "$dep_man_approach" = 'pipenv' ]; then
    # We won't do anything further that needs a lock file.
    python3 -m pipenv install requests --skip-lock
fi

cd "$script_dir"
python integration_tests/test_deployed_app_functionality.py "$app_url"

# Clarify which branch was tested.
if [ "$target" = pypi ]; then
    echo "\n --- Finished testing latest release from PyPI. ---"
else
    echo "\n--- Finished testing pushed version of simple_deploy.py on branch $current_branch. ---"
fi

# Check if user wants to destroy temp files.
echo ""
while true; do
    read -p "Tear down temporary files? " yn
    case $yn in 
        [Yy]* ) echo "Okay, tearing down..."; tear_down=true; break;;
        [Nn]* ) echo "Okay, leaving files."; tear_down=false; break;;
        * ) echo "Please answer yes or no.";;
    esac
done

# Teardown
if [ "$tear_down" = true ]; then
    echo ""
    echo "Cleaning up:"
    echo "  Destroying Heroku app $app_name..."
    heroku apps:destroy --app "$app_name" --confirm "$app_name"
    echo "  Destroying temporary directory..."
    rm -rf "$tmp_dir"
    echo "...removed temporary directory: $tmp_dir"
fi