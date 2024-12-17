"""Utilities for simple_deploy, to be used by platform-specific plugins.

Note: Some of these utilities are also used in core simple_deploy.
"""

import logging
import re
import subprocess
import shlex
import toml

from django.template.engine import Engine, Context
from django.utils.safestring import mark_safe

from .. import sd_messages
from .sd_config import SDConfig
from .command_errors import SimpleDeployCommandError


# Create sd_config once right here. The attributes are set by simple_deploy,
# and then accessible by plugins. This approach keeps from having to pass the config
# instance between core, plugins, and these utility functions.
sd_config = SDConfig()


def add_file(path, contents):
    """Add a new file to the project.

    This function is meant to be used when adding new files that don't typically
    exist in a Django project that runs locally. For example, a platform-specific
    Dockerfile. See the `add_dockerfile()` method in Fly.io's deployer module.

    If the file does not exist, it is written to the project. If the file already
    exists, the user is prompted for permission to overwrite the file.

    Returns:
    - None

    Raises:
    - SimpleDeployCommandError: If file exists, and user does not give permission
    to overwrite file.
    """

    write_output(f"\n  Looking in {path.parent} for {path.name}...")

    if path.exists():
        proceed = get_confirmation(sd_messages.file_found(path.name))
        if not proceed:
            raise SimpleDeployCommandError(sd_messages.file_replace_rejected(path.name))
    else:
        write_output(f"    File {path.name} not found. Generating file...")

    # File does not exist, or we are free to overwrite it.
    path.write_text(contents)

    msg = f"\n    Wrote {path.name} to {path}"
    write_output(msg)


def modify_file(path, contents):
    """Modify an existing file.

    This function is meant for modifying a file that should already exist, such as
    settings.py. We're not getting permission; if unwanted changes are somehow made,
    the user can use Git to restore the file to its original state.

    Returns:
    - None

    Raises:
    - SimpleDeployCommandError: If file does not exist.
    """
    # Make sure file exists.
    if not path.exists():
        msg = f"File {path.as_posix()} does not exist."
        raise SimpleDeployCommandError(msg)

    # Rewrite file with new contents.
    path.write_text(contents)
    msg = f"  Modified file: {path.as_posix()}"
    write_output(msg)


def modify_settings_file(template_path, context=None):
    """Add a platform-specific settings block to settings.py.

    Provide a path to a template including current settings and the platform-specific
    settings block, and a context dictionary.
    """
    if context is None:
        context = {}
    # Add current settings to context.
    settings_string = sd_config.settings_path.read_text()
    safe_settings_string = mark_safe(settings_string)
    context["current_settings"] = safe_settings_string

    modified_settings_string = get_template_string(template_path, context)

    # Write settings to file.
    modify_file(sd_config.settings_path, modified_settings_string)


def add_dir(path):
    """Write a new directory to the file.

    This function is meant to be used when adding new directories that don't
    typically exist in a Django project. For example, a platform-specific directory
    such as .platform/ for Platform.sh.

    Only adds the directory; does nothing if the directory already exists.

    Returns:
    - None
    """
    write_output(f"\n  Looking for {path.as_posix()}...")

    if path.exists():
        write_output(f"    Found {path.as_posix()}")
    else:
        path.mkdir()
        write_output(f"    Added new directory: {path.as_posix()}")


def get_numbered_choice(prompt, valid_choices, quit_message):
    """Select from a numbered list of choices.

    This is used, for example, to select from a number of apps that the user
    has created on a platform.
    """
    prompt += "\n\nYou can quit by entering q.\n"

    while True:
        # Show prompt and get selection.
        log_info(prompt)

        selection = input(prompt)
        log_info(selection)

        if selection.lower() in ["q", "quit"]:
            raise SimpleDeployCommandError(quit_message)

        # Make sure they entered a number
        try:
            selection = int(selection)
        except ValueError:
            msg = "Please enter a number from the list of choices."
            write_output(msg)
            continue

        # Validate selection.
        if selection not in valid_choices:
            msg = "  Invalid selection. Please try again."
            write_output(msg)
            continue

        return selection


def run_quick_command(cmd, check=False, skip_logging=False):
    """Run a command that should finish quickly.

    Commands that should finish quickly can be run more simply than commands that
    will take a long time. For quick commands, we can capture output and then deal
    with it however we like, and the user won't notice that we first captured
    the output.

    The `check` parameter is included because some callers will need to handle
    exceptions. For example, see prep_automate_all() in deploy_platformsh.py. Most
    callers will only check stderr, or maybe the returncode; they won't need to
    involve exception handling.

    Returns:
        CompletedProcess

    Raises:
        CalledProcessError: If check=True is passed, will raise CalledProcessError
        instead of returning a CompletedProcess instance with an error code set.
    """
    if not skip_logging:
        log_info(f"\n{cmd}")

    if sd_config.on_windows:
        output = subprocess.run(cmd, shell=True, capture_output=True)
    else:
        cmd_parts = shlex.split(cmd)
        output = subprocess.run(cmd_parts, capture_output=True, check=check)

    return output


def run_slow_command(cmd, skip_logging=False):
    """Run a command that may take some time.

    For commands that may take a while, we need to stream output to the user, rather
    than just capturing it. Otherwise, the command will appear to hang.
    """

    # DEV: This only captures stderr right now.
    # The first call I used this for was `git push heroku`. That call writes to
    # stderr; I believe streaming to stdout and stderr requires multithreading. The
    # current approach seems to be working for all calls that use it.
    #
    # Adding a parameter stdout=subprocess.PIPE and adding a separate identical loop
    # over p.stdout misses stderr. Maybe combine the loops with zip()? SO posts on
    # this topic date back to Python2/3 days.
    if not skip_logging:
        log_info(f"\n{cmd}")

    cmd_parts = cmd.split()
    with subprocess.Popen(
        cmd_parts,
        stderr=subprocess.PIPE,
        bufsize=1,
        universal_newlines=True,
        shell=sd_config.use_shell,
    ) as p:
        for line in p.stderr:
            write_output(line, skip_logging=skip_logging)

    if p.returncode != 0:
        raise subprocess.CalledProcessError(p.returncode, p.args)


def get_confirmation(msg="Are you sure you want to do this?", skip_logging=False):
    """Get confirmation for an action.

    Assumes an appropriate message has already been displayed about what is to be
    done. Shows a yes|no prompt. You can pass a different message for the prompt; it
    should be phrased to elicit a yes/no response.

    Returns:
        bool: True if confirmation granted, False if not granted.
    """
    prompt = f"\n{msg} (yes|no) "
    confirmed = ""

    # If doing e2e testing, always return True.
    if sd_config.e2e_testing:
        write_output(prompt, skip_logging=skip_logging)
        msg = "  Confirmed for e2e testing..."
        write_output(msg, skip_logging=skip_logging)
        return True

    if sd_config.unit_testing:
        write_output(prompt, skip_logging=skip_logging)
        msg = "  Confirmed for unit testing..."
        write_output(msg, skip_logging=skip_logging)
        return True

    while True:
        write_output(prompt, skip_logging=skip_logging)
        confirmed = input()

        # Log user's response before processing it.
        write_output(confirmed, skip_logging=skip_logging, write_to_console=False)

        if confirmed.lower() in ("y", "yes"):
            return True
        elif confirmed.lower() in ("n", "no"):
            return False
        else:
            write_output("  Please answer yes or no.", skip_logging=skip_logging)


def check_settings(platform_name, start_line, msg_found, msg_cant_overwrite):
    """Check if a platform-specific settings block already exists.

    If so, ask if we can overwrite that block. This is much simpler than trying to
    keep track of individual settings.

    Returns:
        None

    Raises:
        SimpleDeployCommandError: If we can't overwrite existing platform-specific
        settings block.
    """
    settings_text = sd_config.settings_path.read_text()

    re_platform_settings = f"(.*)({start_line})(.*)"
    m = re.match(re_platform_settings, settings_text, re.DOTALL)

    if not m:
        log_info(f"No {platform_name}-specific settings block found.")
        return

    # A platform-specific settings block exists. Get permission to overwrite it.
    if not get_confirmation(msg_found):
        raise SimpleDeployCommandError(msg_cant_overwrite)

    # Platform-specific settings exist, but we can remove them and start fresh.
    sd_config.settings_path.write_text(m.group(1))

    msg = f"  Removed existing {platform_name}-specific settings block."
    write_output(msg)


def write_output(output, write_to_console=True, skip_logging=False):
    """Write output to the appropriate places.

    Typically, this is used for writing output to the console as the configuration
    and deployment work is carried out.  Output may be a string, or an instance of
    subprocess.CompletedProcess.

    Output that's passed to this method typically needs to be logged as well, unless
    skip_logging has been passed. This is useful, for example, when writing
    sensitive information to the console.

    Returns:
        None
    """
    output_str = get_string_from_output(output)

    if write_to_console:
        sd_config.stdout.write(output_str)

    if not skip_logging:
        log_info(output_str)


def log_info(output):
    """Log output, which may be a string or CompletedProcess instance."""
    if sd_config.log_output:
        output_str = get_string_from_output(output)
        log_output_string(output_str)


def commit_changes():
    """Commit changes that have been made to the project.

    This should only be called when automate_all is being used.
    """
    if not sd_config.automate_all:
        return

    write_output("  Committing changes...")

    cmd = "git add ."
    output = run_quick_command(cmd)
    write_output(output)

    cmd = 'git commit -m "Configured project for deployment."'
    output = run_quick_command(cmd)
    write_output(output)


def add_packages(package_list):
    """Add a set of packages to the project's requirements.

    This is a simple wrapper for add_package(), to make it easier to add multiple
    requirements at once. If you need to specify a version for a particular package,
    use add_package().

    Returns:
        None
    """
    for package in package_list:
        add_package(package)


def add_package(package_name, version=""):
    """Add a package to the project's requirements, if not already present.

    Handles calls with version information with pip formatting:
        add_package("psycopg2", version="<2.9")
    The utility helpers handle this version information correctly for the dependency
    management system in use.

    Returns:
        None
    """
    write_output(f"\nLooking for {package_name}...")

    if package_name in sd_config.requirements:
        write_output(f"  Found {package_name} in requirements file.")
        return

    if sd_config.pkg_manager == "pipenv":
        add_pipenv_pkg(sd_config.pipfile_path, package_name, version)
    elif sd_config.pkg_manager == "poetry":
        _check_poetry_deploy_group()
        add_poetry_pkg(sd_config.pyprojecttoml_path, package_name, version)
    else:
        add_req_txt_pkg(sd_config.req_txt_path, package_name, version)

    write_output(f"  Added {package_name} to requirements file.")


def get_template_string(template_path, context):
    """Given a template and context, return contents as a string.

    Contents can then be written to a file.

    Returns:
    - Str: single string representing contents of the rendered template.
    """
    my_engine = Engine()
    template = my_engine.from_string(template_path.read_text())
    return template.render(Context(context))


# --- Helper functions ---


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
        line = _strip_secret_key(line)
        logging.info(line)


def _strip_secret_key(line):
    """Strip secret key value from log file lines."""
    if "SECRET_KEY =" in line:
        new_line = line.split("SECRET_KEY")[0]
        new_line += "SECRET_KEY = *value hidden*"
        return new_line
    else:
        return line


def add_pipenv_pkg(pipfile_path, package, version):
    """Add a package to Pipfile."""
    # A method in simple_deploy may pass an empty string, which would override a
    # default argument value of "*".
    if not version:
        version = "*"

    data = toml.load(pipfile_path)
    data["packages"][package] = version
    data_str = toml.dumps(data)
    pipfile_path.write_text(data_str)


def _check_poetry_deploy_group():
    """Make sure a deploy group exists in pyproject.toml."""
    pptoml_data = toml.load(sd_config.pyprojecttoml_path)
    try:
        deploy_group = pptoml_data["tool"]["poetry"]["group"]["deploy"]
    except KeyError:
        create_poetry_deploy_group(sd_config.pyprojecttoml_path)
        msg = "    Added optional deploy group to pyproject.toml."
        write_output(msg)


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


def add_req_txt_pkg(req_txt_path, package, version):
    """Add a package to requirements.txt."""
    contents = req_txt_path.read_text()
    pkg_string = f"\n{package + version}"
    req_txt_path.write_text(contents + pkg_string)
