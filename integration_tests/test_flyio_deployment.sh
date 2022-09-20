# --- Test the Fly.io deployment process. ---
#
# This is sourced by autoconfigure_deploy_test.sh, so this script has access
#   to all variables defined in autoconfigure_deploy_test.sh.
#
# Note: The test process installs the current development version of django-simple-deploy
#   to deploy the sample project. Fly.io installs the latest pypi release, but never
#   uses it. It's listed in INSTALLED_APPS, so it needs to be able to be installed,
#   but it's never used on Fly.io.
#
# This script is fairly short, because the deployment process is really simple using
#   django-simple-deploy. This script really just runs the simple_deploy command, and
#   a little more if not using automate_all, and then calls a separate script to test
#   the deployed app. It then offers to tear down the local tmp project and the
#   newly-deployed app.

# Create fly_io project; skip if testing --automate-all.
if [ "$test_automate_all" != true ]; then
    echo "\n\nCreating a project on Fly.io..."
    
    # Create an app, and get app name.
    fly_create_output=$(flyctl apps create --generate-name)

    # DEV: Write a more targeted re.
    #   This works in online bash testers, but not on my macOS:
    #   '(New app created: )(\w+\-\w+\-\d{4})'
    re_app_name='(New app created: )(.*)'
    [[ $fly_create_output =~ $re_app_name ]]
    app_name=${BASH_REMATCH[2]}
fi

echo "Running manage.py simple_deploy..."
if [ "$test_automate_all" = true ]; then
    python manage.py simple_deploy --platform fly_io --automate-all --integration-testing
else
    python manage.py simple_deploy --platform fly_io --integration-testing
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

    echo "Deploying to Fly.io..."
    # DEV: Not sure if `fly login` should be run here, or if it will 
    #   be called automatically if needed.

    fly deploy

    # Open project and get URL, for testing.
    fly_open_output=$(flyctl open)

    re_url='(opening )(http.*)( \.\.\.)'
    [[ $fly_open_output =~ $re_url ]]
    url=${BASH_REMATCH[2]}
    project_url=$(echo "$url" | sed 's/http/https/')
    echo " Project URL: $project_url"
fi

# If we're testing automate_all, we need to grab the app name in order
#   to destroy the project later. We also need to get the url for testing.
if [ "$test_automate_all" = true ]; then
    # Get project id from project:info.
    project_info=$(platform project:info)
    id_regex='\| id             \| ([a-z0-9]{13})'
    [[ $project_info =~ $id_regex ]]
    project_id=${BASH_REMATCH[1]}
    echo "  Found project id: $project_id"

    # Open project and get URL.
    project_url=$(platform url --yes)
    echo " Project URL: $project_url"
fi


# Call Python script for functional testing of app.
#   May want to prompt for this.
echo "\n  Testing functionality of deployed app..."

# Fly.io does not return a trailing slash in the URL, which the test script expects.
python test_deployed_app_functionality.py --url "$project_url/"

# Clarify which version was tested.
if [ "$target" = pypi ]; then
    echo "\n --- Finished testing latest release from PyPI. ---"
else
    echo "\n--- Finished testing local development version. ---"
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

    echo "  Destroying Fly.io project..."
    flyctl apps destroy -y $app_name
    echo "  Destroying Fly.io database..."
    flyctl apps destroy -y $app_name-db
    
    echo "  Destroying temporary directory..."
    rm -rf "$tmp_dir"
    echo "...removed temporary directory: $tmp_dir"
fi