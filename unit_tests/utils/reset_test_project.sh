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
[ -f fly.toml ] && rm fly.toml
[ -f Dockerfile ] && rm Dockerfile
[ -f .dockerignore ] && rm .dockerignore

# Platform.sh
[ -f .platform.app.yaml ] && rm .platform.app.yaml
[ -d .platform ] && rm -rf .platform/

# Heroku
[ -f Procfile ] && rm Procfile
[ -d static ] && rm -rf static/

# All platforms
[ -d simple_deploy_logs ] && rm -rf simple_deploy_logs/
[ -d __pycache__ ] && rm -rf __pycache__/
[ -f poetry.lock ] && rm poetry.lock

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

# Commit these changes; helpful in diagnosing failed runs, when you cd into the test
#   project directory and run git status.
git commit -am "Removed unneeded dependency management files."

# --- Add simple_deploy to INSTALLED_APPS. ---
sed -i "" "s/# Third party apps./# Third party apps.\n    'simple_deploy',/" blog/settings.py

# Make sure we have a clean status before calling simple_deploy.
git commit -am "Added simple_deploy to INSTALLED_APPS."