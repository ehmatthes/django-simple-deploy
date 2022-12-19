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

# Build a venv and install requirements.
python3 -m venv b_env
source b_env/bin/activate
pip install --no-index --find-links="$sd_root_dir/vendor/" -r requirements.txt

# Install local version of simple_deploy.
pip install -e "$sd_root_dir/"

# Make it easier to verify what was installed when developing this script.
pip freeze > installed_packages.txt

# Make an initial commit. We call `git branch -m main` because tests may be run
#  on systems where the default branch is something else such as `master` or `trunk`.
#  This applies to contributors' systems, and CI systems. Later tests will expect to 
#  see messages about being on the `main` branch.
git init
git branch -m main
git add .
git commit -am "Initial commit."
git tag -am '' INITIAL_STATE

# Add simple_deploy to INSTALLED_APPS.
sed -i "" "s/# Third party apps./# Third party apps.\n    'simple_deploy',/" blog/settings.py
