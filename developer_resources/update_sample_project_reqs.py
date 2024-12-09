"""Update the requirements for the sample project.

- This assumes uv is available.
- Uses uv to resolve requirements, but `pip download` to populate vendor/.
- uv does not currently support `pip download` (12/2/24).
  See: https://github.com/astral-sh/uv/issues/3163

Note that plugins will need to update some reference files after running this script.
"""

from pathlib import Path
import subprocess
import shlex

# --- Update requirements.txt ---
path_dsd_root = Path(__file__).parents[1]
path_blog_proj = path_dsd_root / "sample_project" / "blog_project"
path_req_in = path_blog_proj / "requirements.in"
path_req_txt = path_blog_proj / "requirements.txt"

assert path_req_in.exists()
assert path_req_txt.exists()

cmd = f"uv pip compile {path_req_in.as_posix()} > {path_req_txt.as_posix()}"
subprocess.run(cmd, shell=True)

# Remove comments, because they just get in the way of testing.
lines_req_txt = path_req_txt.read_text().splitlines()
lines_req_txt = [l for l in lines_req_txt if "#" not in l]
contents = "\n".join(lines_req_txt) + "\n"
path_req_txt.write_text(contents)

# Update vendor/.
path_vendor = path_dsd_root / "vendor"

cmd = f"rm -rf {path_vendor.as_posix()}"
cmd_parts = shlex.split(cmd)
subprocess.run(cmd_parts)

# Make new vendor/ dir.
path_vendor.mkdir()

# Download packages to vendor/.
cmd = f"PIP_REQUIRE_VIRTUALENV='' pip download --dest {path_vendor.as_posix()} -r {path_req_txt.as_posix()}"
subprocess.run(cmd, shell=True)
