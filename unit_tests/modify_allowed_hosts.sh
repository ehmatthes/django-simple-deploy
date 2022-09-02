# Modify the test project instance so the Heroku host is already in ALLOWED_HOSTS.

# Flags:
# -d: full path to temp directory
while getopts d: flag
do
    case "${flag}" in
        d) tmp_dir=${OPTARG};;
    esac
done

# All remaining work is done in the temp dir.
cd "$tmp_dir"
source b_env/bin/activate

# Reset to the initial state of the temp project instance.
git reset --hard INITIAL_STATE
rm Procfile
rm -rf static/

# Add simple_deploy to INSTALLED_APPS.
sed -i "" "s/# Third party apps./# Third party apps.\n    'simple_deploy',/" blog/settings.py

# Start with a non-empty ALLOWED_HOSTS.
sed -i "" "s/ALLOWED_HOSTS = \[\]/ALLOWED_HOSTS = \['herokuapp.com'\]/" blog/settings.py

# Run configuration-only version of simple_deploy.
python manage.py simple_deploy --unit-testing