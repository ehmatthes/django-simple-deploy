# Call simple_deploy with no --platform flag.
#   Should error out, without modifying tmp project at all.

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

# Activate existing venv.
source b_env/bin/activate

# At this point simple_deploy expects `heroku create` to have been run,
#   or expects us to use `--automate-all` to call `heroku create`.
# How mock this call? Need to get output for `heroku apps:info`.

# Run configuration-only version of simple_deploy.
python manage.py simple_deploy --local-test