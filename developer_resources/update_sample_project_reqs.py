"""Update the requirements for the sample project."""

from pathlib import Path
import subprocess
import shlex

# --- Update requirements.txt.
path_blog_proj = Path(__file__).parents[1] / "sample_project" / "blog_project"
path_req_in = path_blog_proj  / "requirements.in"
path_req_txt = path_blog_proj / "requirements.txt"

assert path_req_in.exists()
assert path_req_txt.exists()

cmd_simple = f"uv pip compile {path_req_in.as_posix()}"#" > {path_req_txt.as_posix()}"
cmd = f"uv pip compile {path_req_in.as_posix()} > {path_req_txt.as_posix()}"
# cmd_parts = shlex.split(cmd)

# subprocess.run(cmd_parts, shell=True)

subprocess.run(cmd, shell=True)

# breakpoint()


# Remove comments.


# Update vendor/