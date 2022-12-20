# Reset the test project, so it's ready to be used by another test module.
#   It may be used by a different platform than the previous run.

tmp_dir="$1"
pkg_manager="$2"

# All remaining work is done in the temp dir.
cd "$tmp_dir"

# --- Reset to the initial state of the temp project instance. ---
git reset --hard INITIAL_STATE

# --- Remove any files that may remain. ---
# Fly.io
rm fly.toml
rm Dockerfile
rm .dockerignore

# Platform.sh
rm .platform.app.yaml
rm -rf .platform/

# Heroku
rm Procfile
rm -rf static/

# All platforms
rm -rf simple_deploy_logs/
rum -rf __pycache__/
rm poetry.lock

# --- Remove dependency management files not needed for this package manager. ---
if [ "$pkg_manager" = 'req_txt' ]; then
    rm pyproject.toml
    rm Pipfile
elif [ "$pkg_manager" = 'poetry' ]; then
    rm requirements.txt
    rm Pipfile
elif [ "$pkg_manager" = 'pipenv' ]; then
    rm requirements.txt
    rm pyproject.toml
fi

# --- Add simple_deploy to INSTALLED_APPS. ---
sed -i "" "s/# Third party apps./# Third party apps.\n    'simple_deploy',/" blog/settings.py
