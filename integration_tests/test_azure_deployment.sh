# --- Test the Azure deployment process. ---
#
# This is sourced by autoconfigure_deploy_test.sh, so this script has access
#   to all variables defined in autoconfigure_deploy_test.sh.


# Skip if testing --automate-all
if [ "$test_automate_all" != true ]; then
    echo "Running heroku create..."
    heroku create
fi

echo "Running manage.py simple_deploy..."
# This captures the output of all the work simple_deploy does, so it will contain
#   both the app name and the db server name, and any other information we should need as well.
# If any of this information is difficult to pull, we can generate whatever output is needed 
#   for testing from within simple_deploy. End users will not have any issue with output
#   whose sole purpose is for testing.
if [ "$test_automate_all" = true ]; then
    # Save the output for processing, but display as it's running because it takes a long time.
    output=$(python manage.py simple_deploy --automate-all --platform azure | tee /dev/tty)
else
    python manage.py simple_deploy --platform azure
fi

# Get app name, and db server name.
app_name_pattern='  "defaultHostName": "(learning-log-[a-zA-Z0-9]{16})\.azurewebsites\.net",'
db_pattern='(sd-pg-server-[a-zA-Z0-9]{16})'

echo "Getting app name and db name..."
if [[ "$output" =~ $app_name_pattern ]]; then
    app_name="${BASH_REMATCH[1]}"
    echo "  App name: $app_name"
else
    echo "  Couldn't determine app name."
fi

if [[ "$output" =~ $db_pattern ]]; then
    db_server_name="${BASH_REMATCH[1]}"
    echo "  DB server name: $db_server_name"
else
    echo "  Couldn't find db server name."
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
    # DEV: There should probably be a variable to track which branch we're using on the test repository.
    # git push heroku main
    git push heroku main
    heroku run python manage.py migrate
    heroku open
fi

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
elif [ "$dep_man_approach" = 'poetry' ]; then
    $poetry_cmd add requests
fi

# Define url for testing, from app_name.
app_url="http://$app_name.azurewebsites.net/"
echo "    app url: $app_url"

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

    echo "  Destroying Azure resources..."
    az group delete --name SimpleDeployGroup
    echo "  Destroyed Azure resources."

    # echo "  Destroying Azure db..."
    # az postgres db delete --resource-group SimpleDeployGroup --name $db_server_name --server-name $db_server_name.postgres.database.azure.com
    # echo "  Destroying Azure app..."
    # az webapp delete --resource-group SimpleDeployGroup --name $app_name
    # echo "  Destroying Azure plan..."
    # az appservice plan delete --resource-group SimpleDeployGroup --name SimpleDeployPlan
    # echo "  Destroyed Azure resources."

    echo "  Destroying temporary directory..."
    rm -rf "$tmp_dir"
    echo "...removed temporary directory: $tmp_dir"
fi