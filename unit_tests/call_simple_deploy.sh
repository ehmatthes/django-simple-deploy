# Call simple_deploy for the given platform.

# Flags:
# -d: full path to temp directory
while getopts d:p:s: flag
do
    case "${flag}" in
        d) tmp_dir=${OPTARG};;
        p) target_platform=${OPTARG};;
        s) sd_root_dir=${OPTARG};;
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

# Run configuration-only version of simple_deploy.
# The flags and other conditions vary for testing different platforms, so
#   call each in its own if block.
if [ "$target_platform" = platform_sh ]; then
    # Deployment to Platform.sh currently requires local installation of
    #   platformshconfig.
    pip install --no-index --find-links="$sd_root_dir/vendor/" platformshconfig
    # Test use of a custom deployed project name.
    python manage.py simple_deploy --local-test --platform "$target_platform" --deployed-project-name my_blog_project
elif [ "$target_platform" = heroku ]; then
    python manage.py simple_deploy --local-test --platform "$target_platform"
fi
