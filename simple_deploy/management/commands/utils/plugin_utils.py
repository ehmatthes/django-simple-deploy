"""Utilities for simple_deploy, to be used by platform-specific plugins.

Note: Some of these utilities are also used in core simple_deploy.
"""
import subprocess
import shlex

from django.template.engine import Engine, Context
from django.core.management.base import CommandError

from .. import sd_messages

# --- Utilities that require an instance of Command ---


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


def add_file(sd_command, path, contents):
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

    sd_command.write_output(f"\n  Looking in {path.parent} for {path.name}...")

    if path.exists():
        proceed = sd_command.get_confirmation(sd_messages.file_found(path.name))
        if not proceed:
            raise SimpleDeployCommandError(
                sd_command, sd_messages.file_replace_rejected(path.name)
            )
    else:
        sd_command.write_output(f"    File {path.name} not found. Generating file...")

    # File does not exist, or we are free to overwrite it.
    path.write_text(contents)

    msg = f"\n    Wrote {path.name} to {path}"
    sd_command.write_output(msg)


def modify_file(sd_command, path, contents):
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
        raise SimpleDeployCommandError(sd_command, msg)

    # Rewrite file with new contents.
    path.write_text(contents)
    msg = f"  Modified file: {path.as_posix()}"
    sd_command.write_output(msg)


def add_dir(sd_command, path):
    """Write a new directory to the file.

    This function is meant to be used when adding new directories that don't
    typically exist ina Django project. For example, a platform-specific directory
    such as .platform/ for Platform.sh.

    Only adds the directory; does nothing if the directory already exists.

    Returns:
    - None
    """
    sd_command.write_output(f"\n  Looking for {path.as_posix()}...")

    if path.exists():
        sd_command.write_output(f"    Found {path.as_posix()}")
    else:
        path.mkdir()
        sd_command.write_output(f"    Added new directory: {path.as_posix()}")


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

def run_quick_command(sd_command, cmd, check=False, skip_logging=False):
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
        sd_command.log_info(f"\n{cmd}")

    if sd_command.on_windows:
        output = subprocess.run(cmd, shell=True, capture_output=True)
    else:
        cmd_parts = shlex.split(cmd)
        output = subprocess.run(cmd_parts, capture_output=True, check=check)

    return output

def run_slow_command(sd_command, cmd, skip_logging=False):
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
        sd_command.log_info(f"\n{cmd}")

    cmd_parts = cmd.split()
    with subprocess.Popen(
        cmd_parts,
        stderr=subprocess.PIPE,
        bufsize=1,
        universal_newlines=True,
        shell=sd_command.use_shell,
    ) as p:
        for line in p.stderr:
            sd_command.write_output(line, skip_logging=skip_logging)

    if p.returncode != 0:
        raise subprocess.CalledProcessError(p.returncode, p.args)


# --- Utilities that do not require an instance of Command ---
# Note: These utilities are much easier to test, and should
# be preferred when possible.


def get_template_string(template_path, context):
    """Given a template and context, return contents as a string.

    Contents can then be written to a file.

    Returns:
    - Str: single string representing contents of the rendered template.
    """
    my_engine = Engine()
    template = my_engine.from_string(template_path.read_text())
    return template.render(Context(context))
