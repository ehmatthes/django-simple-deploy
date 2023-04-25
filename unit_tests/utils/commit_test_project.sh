#!/usr/bin/env bash 
# Make a new commit on the test project.

tmp_dir="$1"
commit_msg="$2"

# All remaining work is done in the temp dir.
#   We don't need to activate the enviromment in order to make a commit.
cd "$tmp_dir" || { echo "Temporary Directory $tmp_dir access failed"; exit 1; }

git add .
git commit -am "$commit_msg"
