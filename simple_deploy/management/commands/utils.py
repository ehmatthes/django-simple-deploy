"""Utility functions and classes for simple_deploy.py.

Also contains resources useful to multiple platform-specific deployment 
scripts.
"""

from pathlib import Path
import inspect, re, sys, subprocess, logging

from django.template.engine import Engine
from django.template.utils import get_app_template_dirs
from django.core.management.base import CommandError


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
    modify simple_deploy.execute_subp_run() to accomodate the necessary args.
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

def git_status_okay(status_output, diff_output):
    """Look for uncommmitted changes that aren't related to simple_deploy.

    If the only change is adding "simple_deploy" to INSTALLED_APPS, okay to proceed.
    Only acceptable changes:
        Adding simple_deploy_logs/ to project.
        Adding "simple_deploy" to INSTALLED_APPS;
        Adding "simple_deploy_logs/" to .gitignore.

    Returns:
        True: If okay to proceed.
        False: If not okay to proceed.
    """

    if not check_status_output(status_output, diff_output):
        return False

    return True

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
    if any([path.name not in allowed_modifications for path in modifed_paths]):
        return False

    print(paths)

    # Parse git diff output.
    file_diffs = diff_output.split("\ndiff ")
    for diff in file_diffs:
        diff_lines = diff.split("\n")
        if "settings.py" in diff_lines[0]:
            # parse settings mods
            pass
        elif ".gitignore" in diff_lines[0]:
            # parse .gitignore mods
            pass

    # No reason not to continue.
    return True

def parse_settings_diff(diff_lines):
    """Look for any unexpected changes in settings.py."""
    # Return False or None. True?
    pass

def parse_gitignore_diff(diff_lines):
    """Look for any unexpected changes in .gitignore."""
    pass






def git_diff_okay(status_output_str, diff_output_str):
    """Check the output of `git diff`.

    If the only change is adding "simple_deploy" to INSTALLED_APPS, okay to proceed.
    Only acceptable changes:
        Adding "simple_deploy" to INSTALLED_APPS;
        Adding "simple_deploy_logs/" to .gitignore.

    Returns:
        True: If okay to proceed.
        False: If not okay to proceed.
    """
    # If any lines start with '- ', there are deletions.
    if diff_output_str.count('\n- ') > 1:
        return False



    #If more than one line starts
    # with '+ ', there are multiple additions. Return False for both conditons.
    num_additions = output_str.count('\n+ ')

    if (num_deletions > 0) or (num_additions > 1):
        return False

    # There's only one addition. If it's adding simple_deploy to INSTALLED_APPS, return
    # True.
    re_diff = r"""(\n\+{1}\s+[',"]simple_deploy[',"],)"""
    m = re.search(re_diff, output_str)
    if m:
        return True




    #     If there's only one addition, and it's 'simple_deploy' being added to
    #     INSTALLED_APPS, we can continue.