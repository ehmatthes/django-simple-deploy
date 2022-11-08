# Call simple_deploy for the given platform.

tmp_dir="$1"
invalid_sd_command="$2"

# All remaining work is done in the temp dir.
cd "$tmp_dir"

# Activate existing venv.
source b_env/bin/activate

# Make invalid call.
$invalid_sd_command
