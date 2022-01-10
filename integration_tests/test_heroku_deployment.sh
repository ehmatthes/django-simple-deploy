# --- Test the Heroku deployment process. ---
#
# This is sourced by autoconfigure_deploy_test.sh, so this script has access
#   to all variables defined in autoconfigure_deploy_test.sh.


# Skip if testing --automate-all
if [ "$test_automate_all" != true ]; then
    echo "Running heroku create..."
    heroku create
fi

echo "Running manage.py simple_deploy..."
if [ "$test_automate_all" = true ]; then
    python manage.py simple_deploy --automate-all
else
    python manage.py simple_deploy
fi

# After running simple_deploy, need to regenerate the lock file.
if [ "$dep_man_approach" = 'pipenv' ]; then
    python3 -m pipenv lock
fi

# Heroku (and assume other platforms) needs a copy of requirements with
#   the same django-simple-deploy we're testing against.
#   Modify django-simple-deploy to match install_address.
#   This is important to verify, so we'll routinely include it in the test output.
#   This is only needed if we're testing against a GitHub repo.
#   Note: Pipenv and Poetry specify install address, so this modification is
#     not necessary for either of those approaches.
if [ "$target" = 'current_branch' ]; then
    if [ "$dep_man_approach" = 'req_txt' ]; then
        echo "\nOriginal requirements.txt; should see django-simple-deploy:"
        cat requirements.txt

        echo "  Modifying requirements.txt to require the current branch version on Heroku..."
        sed -i "" "s|django-simple-deploy|$install_address|" requirements.txt

        echo "\nModified requirements.txt; should see django-simple-deploy address you're trying to test:"
        cat requirements.txt
    fi
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
# DEV: Skip this for now; sample project already has requests.
# if [ "$dep_man_approach" = 'req_txt' ]; then
#     pip install requests
# elif [ "$dep_man_approach" = 'pipenv' ]; then
#     # We won't do anything further that needs a lock file.
#     python3 -m pipenv install requests --skip-lock
# elif [ "$dep_man_approach" = 'poetry' ]; then
#     $poetry_cmd add requests
# fi

# cd "$script_dir"
# python integration_tests_new/test_deployed_app_functionality.py --url "$app_url"
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
    echo "  Destroying Heroku app $app_name..."
    heroku apps:destroy --app "$app_name" --confirm "$app_name"
    echo "  Destroying temporary directory..."
    rm -rf "$tmp_dir"
    echo "...removed temporary directory: $tmp_dir"
fi