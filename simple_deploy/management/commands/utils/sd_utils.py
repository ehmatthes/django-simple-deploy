"""Utility functions and classes for simple_deploy.py.

Utilities in this module should only be used internally by simple_deploy.
Any utility used by plugins should be moved to plugin_utils.py.
"""

from pathlib import Path
import inspect, re, sys, subprocess, logging
from importlib.metadata import packages_distributions

from django.template.engine import Engine, Context
from django.template.utils import get_app_template_dirs

from .command_errors import SimpleDeployCommandError

import toml


def validate_choice(choice, valid_choices):
    """Validate a choice made by the user."""
    if choice in valid_choices:
        return True
    return False


def get_plugin_name():
    """Get the name of the installed plugin."""
    available_packages = packages_distributions().keys()
    return _get_plugin_name_from_packages(available_packages)


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
    """Get a list of requirements that are already in Pipfile.

    Parses Pipfile, because we don't want to trust a lock file, and we need to examine
    packages that may be listed in Pipfile but not currently installed.

    This is a one-line utility, but having it here allows for easier testing, and makes
    it easier to expand this to manage a deploy group if appropriate.
    """
    return toml.load(path)["packages"].keys()


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

    if not _check_git_diff(diff_output):
        return False

    # No reason not to continue.
    return True


# --- Helper functions ---


def _check_git_diff(diff_output):
    """Check git diff output, which may include several changed files."""
    file_diffs = diff_output.split("\ndiff ")
    for diff in file_diffs:
        diff_lines = diff.split("\n")
        if "settings.py" in diff_lines[0]:
            if not _check_settings_diff(diff_lines):
                return False
        elif ".gitignore" in diff_lines[0]:
            if not _check_gitignore_diff(diff_lines):
                return False

    return True


def _check_settings_diff(diff_lines):
    """Look for any unexpected changes in settings.py.

    Note: May want to accept a platform-specific settings block.
    """
    lines = _clean_diff(diff_lines)

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


def _check_gitignore_diff(diff_lines):
    """Look for any unexpected changes in .gitignore."""
    lines = _clean_diff(diff_lines)

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


def _clean_diff(diff_lines):
    """Remove unneeded info from diff output."""
    # Get rid of blank lines. Most likely a newline at end of output.
    lines = [l for l in diff_lines if l]

    # Get rid of lines that start with --- or +++
    # Also, get rid of line starting with -- from split() removing first occurrence of
    # "diff".
    lines = [l for l in lines if l[:2] not in ("--", "++")]

    # Only keep lines indicating changes.
    lines = [l for l in lines if l[0] in ("-", "+")]

    # Ignore additions or deletions of blank lines.
    lines = [l for l in lines if l not in ("-", "+")]

    return lines


def _get_plugin_name_from_packages(available_packages):
    """Helper for getting plugin name from installed packages.

    This is broken into a helper function to make testing easier.
    """
    # Get possible plugin names.
    plugin_prefix = f"dsd_"
    plugin_names = [
        pkg_name for pkg_name in available_packages if plugin_prefix in pkg_name
    ]
    if len(plugin_names) == 0:
        msg = f"Could not find any plugins. Officially-supported plugins are:" ""
        msg += "\n  dsd-flyio dsd-platformsh dsd-heroku"
        msg += "\nYou can install any of these with pip:"
        msg += "\n  $ pip install dsd-flyio"
        msg += "\nPlease install the plugin for the platform you want to deploy to,"
        msg += "\nand then run the deploy command again."
        raise SimpleDeployCommandError(msg)

    if len(plugin_names) == 1:
        return plugin_names[0]

    # At this point, it's simply an error if the user has installed multiple plugins.
    msg = f"There seem to be multiple plugins installed."
    msg += "\nPlease uninstall plugins, keeping only the one you want to use for deployment."
    msg += "\nFuture releases of simple_deploy may allow you to select which plugin to use."
    raise SimpleDeployCommandError(msg)
