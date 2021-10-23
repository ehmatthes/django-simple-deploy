# Test the simple_deploy process for deployment on Heroku.

# Overall approach:
# - Create a temporary working location, outside of any existing git repo.
# - Clone the test instance of the LL project.
# - Build a Python venv.
# - Follow the deploy steps.
# - Run automated availability and functionality tests.
#   - This could be a call to a .py file
# - Pause to let user test deployed project.
# - Prompt for whether to destroy deployed app (default yes).
# - Destroy temp project.

# Make sure user is okay with building a temp environment in $HOME.
echo ""
echo "This test will build a temporary directory in your home folder."
while true; do
    read -p "Proceed? " yn
    case $yn in 
        [Yy]* ) echo "Okay, proceeding with tests..."; break;;
        [Nn]* ) echo "Okay, not running tests."; exit;;
        * ) echo "Please answer yes or no.";;
    esac
done

# Make tmp location and clone LL test repo.
echo "Building temp environment and cloning LL project:"

script_dir=$(pwd)
tmp_dir="$HOME/tmp_django_simple_deploy_test"
mkdir "$tmp_dir"
echo "  Made temporary directory: $tmp_dir"

echo "Cloning LL project into tmp directory..."
git clone https://github.com/ehmatthes/learning_log_heroku_test.git $tmp_dir

# Need a Python environment for configuring project.
# This environment needs to be deactivated before running the Python testing
#   script below.
# 
echo "Building Python environment..."
cd "$tmp_dir"
python3 -m venv ll_env
source ll_env/bin/activate
pip install -r requirements.txt

echo "Initializing Git repostitory..."
git init
git add .
git commit -am "Initial commit."

# Now install django-simple-deploy, just as a user would.
echo "Installing django-simple-deploy..."
pip install git+git://github.com/ehmatthes/django-simple-deploy

echo "Adding simple_deploy to INSTALLED_APPS..."
sed -i "" "s/# Third party apps./# Third party apps.\n    'simple_deploy',/" learning_log/settings.py

echo "Running heroku create..."
heroku create

echo "Running manage.py simple_deploy..."
python manage.py simple_deploy

echo "Committing changes..."
git add .
git commit -am "Configured for deployment."

echo "Pushing to heroku..."
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
echo "  Testing functionality of deployed app..."
# Need requests to run functionality tests.
#   This uses the same venv that was built for deploying the project.
pip install requests
cd "$script_dir"
python test_deployed_app_functionality.py "$app_url"

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