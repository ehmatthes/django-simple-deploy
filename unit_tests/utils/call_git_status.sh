# Call git status on the test project.

tmp_dir="$1"

# All remaining work is done in the temp dir.
#   We don't need to activate the enviromment in order to check git status.
cd "$tmp_dir"

git status