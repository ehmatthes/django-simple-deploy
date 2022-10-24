# --- Test the Heroku deployment process. ---
#
# This is sourced by autoconfigure_deploy_test.sh, so this script has access
#   to all variables defined in autoconfigure_deploy_test.sh.
#
# Note: The test process installs the current development version of django-simple-deploy
#   to deploy the sample project. Heroku installs the latest pypi release, but never
#   uses it. It's listed in INSTALLED_APPS, so it needs to be able to be installed,
#   but it's never used on Heroku.
#
# This script is fairly short, because the deployment process is really simple using
#   django-simple-deploy. This script really just runs the simple_deploy command, and
#   a little more if not using automate_all, and then calls a separate script to test
#   the deployed app. It then offers to tear down the local tmp project and the
#   newly-deployed app.


# Skip if testing --automate-all
if [ "$test_automate_all" != true ]; then
    echo "Running heroku create..."
    heroku create
fi

echo "Running manage.py simple_deploy..."
if [ "$test_automate_all" = true ]; then
    python manage.py simple_deploy --automate-all --platform heroku --integration-testing
else
    python manage.py simple_deploy --platform heroku --integration-testing
fi

# After running simple_deploy, need to regenerate the lock file.
if [ "$dep_man_approach" = 'pipenv' ]; then
    python3 -m pipenv lock
fi

# Skip if testing --automate-all.
if [ "$test_automate_all" != true ]; then
    echo "\n\nCommitting changes..."
    git add .
    git commit -am "Configured for deployment."

    echo "Pushing to heroku..."
    git push heroku main
    heroku run python manage.py migrate
    heroku open
fi

app_name=$(heroku apps:info | grep "===")
app_name=${app_name:4}
echo "  Heroku app name: $app_name"

app_url=$(heroku apps:info | grep "Web URL")
app_url=${app_url:16}
echo "  Heroku URL: $app_url"

# Call Python script for functional testing of app.
#   May want to prompt for this.
echo "\n  Testing functionality of deployed app..."

python test_deployed_app_functionality.py --url "$app_url"


# Test local functionality.
# Deploying with simple_deploy should not impact local functionality.
echo "\n  Testing local functionality with runserver..."
python manage.py migrate
python manage.py runserver 8008 &>/dev/null &
# Pause to let runserver start; this pause may need to be adjusted to work
#   on everyone's systems.
sleep 1
python test_deployed_app_functionality.py --url "http://localhost:8008/"
# Kill the runserver processes. Calling runserver in the background launches
#   a process, but then Django launches another child process. We want to kill
#   both of these.
# DEV: This is probably OS-specific, and needs to be tested on non-macOS systems.
pkill -f "runserver 8008"
echo "    Finished testing local functionality."


# Clarify which version was tested.
if [ "$target" = pypi ]; then
    echo "\n --- Finished testing latest release from PyPI. ---"
else
    echo "\n--- Finished testing local development version. ---"
fi

# Check if user wants to destroy temp files.
echo ""
if [ "$skip_confirmations" != true ]; then
    while true; do
        read -p "Tear down temporary files? " yn
        case $yn in 
            [Yy]* ) echo "Okay, tearing down..."; tear_down=true; break;;
            [Nn]* ) echo "Okay, leaving files."; tear_down=false; break;;
            * ) echo "Please answer yes or no.";;
        esac
    done
else
    tear_down=true
fi

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