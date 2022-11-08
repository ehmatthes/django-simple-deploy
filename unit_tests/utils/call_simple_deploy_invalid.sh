# Call simple_deploy for the given platform.

# Flags:
# -d: full path to temp directory
# while getopts "d:c:" flag
# do
#     case "${flag}" in
#         d) tmp_dir=${OPTARG};;
#         c) invalid_sd_command="${OPTARG}";;
#     esac
# done

tmp_dir="$1"
invalid_sd_command="$2"

# All remaining work is done in the temp dir.
cd "$tmp_dir"

# Activate existing venv.
source b_env/bin/activate

echo "\n\ntmp_dir: $tmp_dir" >> "$tmp_dir/diagnostics.txt"
echo "\n\ninvalid_sd_command: $invalid_sd_command" >> "$tmp_dir/diagnostics.txt"

$invalid_sd_command
# python manage.py simple_deploy --unit-testing "$arg_string"
# python manage.py simple_deploy --unit-testing

# my_cmd="python manage.py simple_deploy --unit-testing --platform unsupported_platform_name"
# $my_cmd