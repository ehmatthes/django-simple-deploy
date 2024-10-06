"""Utilities for simple_deploy, to be used by platform-specific plugins."""

from django.template.engine import Engine, Context


# --- Utilities that require an instance of Command ---


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
        proceed = sd_command.get_confirmation(sd_command.messages.file_found(path.name))
        if not proceed:
            raise sd_command.SimpleDeployCommandError(
                sd_command, sd_command.messages.file_replace_rejected(path.name)
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
        raise sd_command.SimpleDeployCommandError(sd_command, msg)

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
