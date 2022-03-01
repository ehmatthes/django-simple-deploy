# Set up the test project.

# Flags:
# -d: full path to temp directory
# -s: full path to vendor source directory
while getopts d:s: flag
do
    case "${flag}" in
        d) tmp_dir=${OPTARG};;
        s) src_dir=${OPTARG};;
    esac
done

# Copy sample project to temp dir.
rsync -ar ../sample_project/blog_project/ "$tmp_dir"

# All remaining work is done in the temp dir.
cd "$tmp_dir"

# Set up for testing Heroku deployment.
rm pyproject.toml
rm Pipfile

# Build a venv and install requirements.
python3 -m venv tmp_env
source tmp_env/bin/activate
pip install --no-index --find-links="$src_dir/" -r requirements.txt

