from django.core.management.base import CommandError

# from .plugin_utils import log_info


class SimpleDeployCommandError(CommandError):
    """Simple wrapper around CommandError, to facilitate consistent
    logging of command errors.

    Writes "SimpleDeployCommandError:" and error message to log, then raises
    actual CommandError.

    Note: This changes the exception type from CommandError to
    SimpleDeployCommandError.
    """

    def __init__(self, message):
        from .plugin_utils import log_info

        log_info("\nSimpleDeployCommandError:")
        log_info(message)
        super().__init__(message)
