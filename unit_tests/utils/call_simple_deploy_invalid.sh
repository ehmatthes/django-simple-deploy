# Call simple_deploy for the given platform.

tmp_dir="$1"
invalid_sd_command="$2"

# All remaining work is done in the temp dir.
cd "$tmp_dir"

# Activate existing venv.
source b_env/bin/activate

# Add --unit-testing argument to call.
# We do this here, so the test script can contain the exact invalid calls
#   that we expect users to make.
invalid_sd_command="$(echo "$invalid_sd_command" | sed 's/simple_deploy/simple_deploy --unit-testing/')"

# Make invalid call.
$invalid_sd_command
