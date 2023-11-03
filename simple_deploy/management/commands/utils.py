import inspect, re, sys

from django.template.engine import Engine
from django.template.utils import get_app_template_dirs
from django.core.management.base import CommandError


def write_file_from_template(path, template, context=None):
    """Write a file based on a platform-specific template.
    This may be a whole new file, such as a Dockerfile. Or, we may be modifying
      an existing file such as settings.py.

    Returns:
    - None
    """

    # Get the platform name from the file that's importing this function.
    #   This may need to be moved to its own file if it ends up being imported
    #   from different places.
    caller = inspect.stack()[1].filename
    if sys.platform == 'win32':
        platform_re = r'\\simple_deploy\\management\\commands\\(.*)\\deploy.py'
    else:
        platform_re = r'/simple_deploy/management/commands/(.*)/deploy.py'
    m = re.search(platform_re, caller)
    platform = m.group(1)

    # Make a template engine that can access the platform's templates.
    my_dirs = get_app_template_dirs(f"management/commands/{platform}/templates")
    my_engine = Engine(dirs=my_dirs)

    # Generate the template string, and write it to the given path.
    template_string = my_engine.render_to_string(template, context)
    path.write_text(template_string)


class SimpleDeployCommandError(CommandError):
    """Simple wrapper around CommandError, to facilitate consistent
    logging of command errors.

    Writes "SimpleDeployCommandError:" and error message to log, then raises actual
      CommandError.

    Note: This changes the exception type from CommandError to SimpleDeployCommandError.
    """

    def __init__(self, sd_command, message):
        sd_command.log_info("\nSimpleDeployCommandError:")
        sd_command.log_info(message)
        super().__init__(message)
