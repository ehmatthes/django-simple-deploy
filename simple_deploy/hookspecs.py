import pluggy

hookspec = pluggy.HookspecMarker("simple_deploy")


@hookspec
def automate_all_supported():
    """Specify whether --automate-all is supported on the specified platform."""


@hookspec
def simple_deploy_get_automate_all_msg():
    """Get a platform-specific message for confirming the --automate-all option."""


@hookspec
def simple_deploy_deploy(sd):
    """Carry out all platform-specific configuration and deployment work."""
