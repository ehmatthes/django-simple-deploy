# Call simple_deploy for the given platform.

# Flags:
# -d: full path to temp directory
while getopts d: flag
do
    case "${flag}" in
        d) tmp_dir=${OPTARG};;
        # a) arg_string=${OPTARG};;
    esac
done

# All remaining work is done in the temp dir.
cd "$tmp_dir"

# Activate existing venv.
source b_env/bin/activate

# python manage.py simple_deploy --unit-testing "$a"
python manage.py simple_deploy --unit-testing
