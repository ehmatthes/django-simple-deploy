# --- Test the Azure deployment process. ---
#
# This is sourced by autoconfigure_deploy_test.sh, so this script has access
#   to all variables defined in autoconfigure_deploy_test.sh.
#
# The Azure deployment process only works with the --automate-all flag. If this
#   test is run without that flag, present a message and exit. (This should already
#   happen in hte test_deploy_process.sh script.)


echo "Running manage.py simple_deploy..."
# This captures the output of all the work simple_deploy does, so it will contain
#   both the app name and the db server name, and any other information we should need as well.
# If any of this information is difficult to pull, we can generate whatever output is needed 
#   for testing from within simple_deploy. End users will not have any issue with output
#   whose sole purpose is for testing.

# Save the output for processing, but display as it's running because it takes a long time.
#   When debugging, it's sometimes helpful to not store the output and see more immediately.
output=$(python manage.py simple_deploy --automate-all --platform azure --azure-plan-sku $azure_plan_sku | tee /dev/tty)

# Get app name, and db server name.
app_name_pattern='  "defaultHostName": "(blog-[a-zA-Z0-9]{16})\.azurewebsites\.net",'
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

# Call Python script for functional testing of app.
#   May want to prompt for this.
echo "\n  Testing functionality of deployed app..."

# Define url for testing, from app_name.
app_url="http://$app_name.azurewebsites.net/"
echo "    app url: $app_url"

python test_deployed_app_functionality.py --url "$app_url"

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
    echo "    Deleting SimpleDeployGroup..."
    az group delete --name SimpleDeployGroup
    echo "    Destroyed Azure resources."

    echo "  Destroying temporary directory..."
    rm -rf "$tmp_dir"
    echo "...removed temporary directory: $tmp_dir"
fi