# Set up the test project.

# Flags:
# -d: full path to temp directory
# -s: full path to vendor source directory
while getopts d:s: flag
do
    case "${flag}" in
        d) tmp_dir=${OPTARG};;
        s) sd_root_dir=${OPTARG};;
    esac
done

# Copy sample project to temp dir.
rsync -ar ../sample_project/blog_project/ "$tmp_dir"

# All remaining work is done in the temp dir.
cd "$tmp_dir"

# Set up for testing Heroku deployment.
rm pyproject.toml
rm Pipfile

# Build a venv and install requirements.
python3 -m venv b_env
source b_env/bin/activate
pip install --no-index --find-links="$sd_root_dir/vendor/" -r requirements.txt

# Install local version of simple_deploy.
pip install -e "$sd_root_dir/"

# Make it easier to verify what was installed when developing this script.
pip freeze > installed_packages.txt

# Make an initial commit.
git init
git add .
git commit -am "Initial commit."
git tag -am '' INITIAL_STATE

# Add simple_deploy to INSTALLED_APPS.
sed -i "" "s/# Third party apps./# Third party apps.\n    'simple_deploy',/" blog/settings.py

# At this point simple_deploy expects `heroku create` to have been run,
#   or expects us to use `--automate-all` to call `heroku create`.
# How mock this call? Need to get output for `heroku apps:info`.

# Run configuration-only version of simple_deploy.
python manage.py simple_deploy --local-test