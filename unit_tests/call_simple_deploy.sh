# Call simple_deploy for the given platform.

# Flags:
# -d: full path to temp directory
while getopts d:p: flag
do
    case "${flag}" in
        d) tmp_dir=${OPTARG};;
        p) target_platform=${OPTARG}
    esac
done

# All remaining work is done in the temp dir.
cd "$tmp_dir"

# Activate existing venv.
source b_env/bin/activate

# For testing deployment to Heroku:
# At this point simple_deploy expects `heroku create` to have been run,
#   or expects us to use `--automate-all` to call `heroku create`.
# How mock this call? Need to get output for `heroku apps:info`.

# Deployment to Platform.sh currently requires local installation of
#   platformshconfig.
if [ "$target_platform" = platform_sh ]; then
    pip install platformshconfig
fi

# Run configuration-only version of simple_deploy.
python manage.py simple_deploy --local-test --platform "$target_platform"