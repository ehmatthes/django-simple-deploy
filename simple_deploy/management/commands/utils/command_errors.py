from django.core.management.base import CommandError


class SimpleDeployCommandError(CommandError):
    """Simple wrapper around CommandError, to facilitate consistent
    logging of command errors.

    Writes "SimpleDeployCommandError:" and error message to log, then raises
    actual CommandError.

    Note: This changes the exception type from CommandError to
    SimpleDeployCommandError.
    """

    def __init__(self, message):
        """Log the error, and then raise a standard CommandError."""

        # Importing plugin_utils or log_info at the module level causes a circular
        # import error, because plugin_utils imports SimpleDeployCommandError.
        # This seems like a reasonable place to avoid the circular import.
        from .plugin_utils import log_info

        log_info("\nSimpleDeployCommandError:")
        log_info(message)
        super().__init__(message)
