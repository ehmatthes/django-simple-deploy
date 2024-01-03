"""Utility functions and classes for simple_deploy.py.

Also contains resources useful to multiple platform-specific deployment 
scripts.
"""

from pathlib import Path
import inspect, re, sys, subprocess, logging

from django.template.engine import Engine
from django.template.utils import get_app_template_dirs
from django.core.management.base import CommandError

import toml


def write_file_from_template(path, template, context=None):
    """Write a file based on a platform-specific template.
    This may be a whole new file, such as a Dockerfile. Or, we may be
    modifying an existing file such as settings.py.

    Returns:
    - None
    """

    # Get the platform name from the file that's importing this function.
    #   This may need to be moved to its own file if it ends up being imported
    #   from different places.
    caller = inspect.stack()[1].filename
    if sys.platform == "win32":
        platform_re = r"\\simple_deploy\\management\\commands\\(.*)\\deploy.py"
    else:
        platform_re = r"/simple_deploy/management/commands/(.*)/deploy.py"
    m = re.search(platform_re, caller)
    platform = m.group(1)

    # Make a template engine that can access the platform's templates.
    my_dirs = get_app_template_dirs(f"management/commands/{platform}/templates")
    my_engine = Engine(dirs=my_dirs)

    # Generate the template string, and write it to the given path.
    template_string = my_engine.render_to_string(template, context)
    path.write_text(template_string)


def get_numbered_choice(sd_command, prompt, valid_choices, quit_message):
    """Select from a numbered list of choices.

    This is used, for example, to select from a number of apps that the user
    has created on a platform.
    """
    prompt += "\n\nYou can quit by entering q.\n"

    while True:
        # Show prompt and get selection.
        sd_command.log_info(prompt)

        selection = input(prompt)
        sd_command.log_info(selection)

        if selection.lower() in ["q", "quit"]:
            raise SimpleDeployCommandError(sd_command, quit_message)

        # Make sure they entered a number
        try:
            selection = int(selection)
        except ValueError:
            msg = "Please enter a number from the list of choices."
            sd_command.write_output(msg)
            continue

        # Validate selection.
        if selection not in valid_choices:
            msg = "  Invalid selection. Please try again."
            sd_command.write_output(msg)
            continue

        return selection


def validate_choice(choice, valid_choices):
    """Validate a choice made by the user."""
    if choice in valid_choices:
        return True
    return False


class SimpleDeployCommandError(CommandError):
    """Simple wrapper around CommandError, to facilitate consistent
    logging of command errors.

    Writes "SimpleDeployCommandError:" and error message to log, then raises
    actual CommandError.

    Note: This changes the exception type from CommandError to
    SimpleDeployCommandError.
    """

    def __init__(self, sd_command, message):
        sd_command.log_info("\nSimpleDeployCommandError:")
        sd_command.log_info(message)
        super().__init__(message)


def get_string_from_output(output):
    """Convert output to string.

    Output may be a string, or an instance of subprocess.CompletedProcess.

    This function assumes that output is either stdout *or* stderr, but not both. If we
    need to display both, consider redirecting stderr to stdout:
        subprocess.run(cmd_parts, stderr=subprocess.STDOUT, ...)
    This has not been necessary yet; if it becomes necessary we'll probably need to
    modify simple_deploy.run_quick_command() to accomodate the necessary args.
    """
    if isinstance(output, str):
        return output

    if isinstance(output, subprocess.CompletedProcess):
        # Extract subprocess output as a string. Assume output is either stdout or
        # stderr, but not both.
        output_str = output.stdout.decode()
        if not output_str:
            output_str = output.stderr.decode()

        return output_str


def log_output_string(output):
    """Log output as a series of single lines, for better log parsing.

    Returns:
        None
    """
    for line in output.splitlines():
        line = strip_secret_key(line)
        logging.info(line)


# --- Helper functions ---


def strip_secret_key(line):
    """Strip secret key value from log file lines."""
    if "SECRET_KEY =" in line:
        new_line = line.split("SECRET_KEY")[0]
        new_line += "SECRET_KEY = *value hidden*"
        return new_line
    else:
        return line


def check_status_output(status_output, diff_output):
    """Check output of `git status --porcelain` for uncommitted changes.

    Look for:
        Untracked changes other than simple_deploy_logs/
        Modified files beyond .gitignore and settings.py
    Consider looking at other status codes at some point.

    Returns:
        bool: True if okay to proceed, False if not.
    """
    lines = status_output.splitlines()
    lines = [line.strip() for line in lines]

    # Process untracked changes first.
    untracked_changes = [line for line in lines if line[0:2] == "??"]

    if len(untracked_changes) > 1:
        return False
    if (
        len(untracked_changes) == 1
        and "simple_deploy_logs/" not in untracked_changes[0]
    ):
        return False

    # Process modified files.
    modified_files = [line.replace("M ", "") for line in lines if line[0] == "M"]
    modified_paths = [Path(f) for f in modified_files]
    allowed_modifications = ["settings.py", ".gitignore"]
    # Return False if any files other than these have been modified.
    if any([path.name not in allowed_modifications for path in modified_paths]):
        return False

    # Parse git diff output.
    file_diffs = diff_output.split("\ndiff ")
    for diff in file_diffs:
        diff_lines = diff.split("\n")
        if "settings.py" in diff_lines[0]:
            if not check_settings_diff(diff_lines):
                return False
        elif ".gitignore" in diff_lines[0]:
            if not check_gitignore_diff(diff_lines):
                return False

    # No reason not to continue.
    return True


def check_settings_diff(diff_lines):
    """Look for any unexpected changes in settings.py.

    Note: May want to accept a platform-specific settings block.
    """
    lines = clean_diff(diff_lines)

    # If no meaningful changes, proceed.
    if not lines:
        return True

    # If there's more than one change to settings, don't proceed.
    if len(lines) > 1:
        return False

    # If the change is not adding simple_deploy, don't proceed.
    if "simple_deploy" not in lines[0]:
        return False

    return True


def check_gitignore_diff(diff_lines):
    """Look for any unexpected changes in .gitignore."""
    lines = clean_diff(diff_lines)

    # If no meaningful changes, proceed.
    if not lines:
        return True

    # If there's more than one change to .gitignore, don't proceed.
    if len(lines) > 1:
        return False

    # If the change is not adding simple_deploy, don't proceed.
    if "simple_deploy_logs" not in lines[0]:
        return False

    return True


def clean_diff(diff_lines):
    """Remove unneeded info from diff output."""
    # Get rid of lines that start with --- or +++
    lines = [l for l in diff_lines if l[:2] not in ("--", "++")]

    # Ignore additions or deletions of blank lines.
    lines = [l.strip() for l in lines]
    lines = [l for l in lines if l]
    lines = [l for l in lines if l not in ("-", "+")]
    # Ignore lines that don't start with - or +.
    try:
        lines = [l for l in lines if l[0] in ("-", "+")]
    except IndexError:
        return []

    return lines


def parse_req_txt(path):
    """Get a list of requirements from a requirements.txt file.

    Parses requirements.txt file directly, rather than using a command like
    `pip list`. `pip list` lists all installed packages, but they may not be in
    requirements.txt, depending on when `pip freeze` was last run. This is different
    than other dependency management systems, which write to various requirements
    files whenever a package is installed.

    Returns:
        List[str]: List of strings representing each requirement.
    """
    lines = path.read_text().splitlines()

    # Remove blank lines, extra whitespace, and comments.
    lines = [l.strip() for l in lines if l]
    lines = [l for l in lines if l[0] != "#"]

    # Parse requirements file, without including version information.
    req_re = r"^([a-zA-Z0-9_\-]*)"
    requirements = []
    for line in lines:
        m = re.search(req_re, line)
        if m:
            requirements.append(m.group(1))

    return requirements


def parse_pipfile(path):
    """Get a list of requirements that are already in the Pipfile.

    Parses Pipfile, because we don't want to trust a lock file, and we need to examine
    packages that may be listed in Pipfile but not currently installed.

    Returns:
        List[str]: List of strings representing each requirement.
    """
    lines = path.read_text().splitlines()

    # Remove blank lines, extra whitespace, and comments.
    lines = [l.strip() for l in lines if l]
    lines = [l for l in lines if l[0] != "#"]

    requirements = []
    in_packages = False
    for line in lines:
        # Ignore all lines until the start of packages. Stop parsing at the next block.
        if "[packages]" in line:
            in_packages = True
            continue
        elif in_packages and line[0] == "[":
            # Ignore dev packages for now.
            break

        if in_packages:
            pkg_name = line.split("=")[0].rstrip()
            requirements.append(pkg_name)

    return requirements


def parse_pyproject_toml(path):
    """Get a list of requirements that Poetry is already tracking.

    Parses pyproject.toml file. It's easier to work with the output of
    `poetry show`, but that examines poetry.lock. We are interested in what's
    written to pyproject.toml, not what's in the lock file.

    Returns:
        List[str]: List of strings representing each requirement.
    """
    parsed_toml = toml.load(path)

    # For now, just examine main requirements and deploy group requirements.
    main_reqs = parsed_toml["tool"]["poetry"]["dependencies"].keys()
    requirements = list(main_reqs)
    try:
        deploy_reqs = parsed_toml["tool"]["poetry"]["group"]["deploy"][
            "dependencies"
        ].keys()
    except KeyError:
        # This group doesn't exist yet, which is fine.
        pass
    else:
        requirements += list(deploy_reqs)

    # Remove python as a requirement, as we're only interested in packages.
    if "python" in requirements:
        requirements.remove("python")

    return requirements


def create_poetry_deploy_group(pptoml_path):
    """Create a deploy group for Poetry in pyproject.toml."""
    pptoml_data = toml.load(pptoml_path)

    # Create Poetry group if needed.
    if "group" not in pptoml_data["tool"]["poetry"]:
        pptoml_data["tool"]["poetry"]["group"] = {}

    # Create optional deploy group, and deploy group dependencies.
    pptoml_data["tool"]["poetry"]["group"]["deploy"] = {"optional": True}
    pptoml_data["tool"]["poetry"]["group"]["deploy"]["dependencies"] = {}

    pptoml_data_str = toml.dumps(pptoml_data)
    pptoml_path.write_text(pptoml_data_str)


def add_poetry_pkg(pptoml_path, package, version):
    """Add a package to poetry deploy group of pyproject.toml."""

    # A method in simple_deploy may pass an empty string, which would override a
    # default argument value of "*".
    if not version:
        version = "*"

    pptoml_data = toml.load(pptoml_path)
    pptoml_data["tool"]["poetry"]["group"]["deploy"]["dependencies"][package] = version

    pptoml_data_str = toml.dumps(pptoml_data)
    pptoml_path.write_text(pptoml_data_str)


def add_pipenv_pkg(pipfile_path, package, version):
    """Add a package to Pipfile."""
    # A method in simple_deploy may pass an empty string, which would override a
    # default argument value of "*".
    if not version:
        version = "*"

    pipfile_text = pipfile_path.read_text()

    # Align comments. Align at column 30; take away name length, and version spec space.
    # tab_string = " " * (30 - len(package) - 5 - len(version))

    # Write package name right after [packages]. For simple projects, this shouldn't
    # cause any issues.
    new_pkg_string = f'[packages]\n{package} = "{version}"'
    pipfile_text = pipfile_text.replace("[packages]", new_pkg_string)

    pipfile_path.write_text(pipfile_text)



    # Use toml.
    # data = toml.load(pipfile_path)
    # data[packages][package_name] = version
    # data_str = toml.dumps(data)
    # pipfile_path.write_text(data_str)
