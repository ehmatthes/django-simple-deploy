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

# Run configuration-only version of simple_deploy.
# The flags and other conditions vary for testing different platforms, so
#   call each in its own if block.
if [ "$target_platform" = fly_io ]; then
    python manage.py simple_deploy --unit-testing --platform "$target_platform" --deployed-project-name my_blog_project
elif [ "$target_platform" = platform_sh ]; then
    # Test use of a custom deployed project name.
    python manage.py simple_deploy --unit-testing --platform "$target_platform" --deployed-project-name my_blog_project
elif [ "$target_platform" = heroku ]; then
    python manage.py simple_deploy --unit-testing --platform "$target_platform"
fi
