# Set up the test project.

while getopts d:s: flag
do
    case "${flag}" in
        d) tmp_dir=${OPTARG};;
        s) src_dir=${OPTARG};;
    esac
done


# Change to the temp dir, create a venv, and install required packages.
cd "$tmp_dir"
python3 -m venv tmp_env
source tmp_env/bin/activate
pip install --no-index --find-links="$src_dir/" requests django django-bootstrap5
pip freeze > requirements.txt

# Copy sample project to temp dir.
