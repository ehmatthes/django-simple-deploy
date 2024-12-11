import pluggy

hookspec = pluggy.HookspecMarker("simple_deploy")


# @hookspec
# def automate_all_supported():
#     """Specify whether --automate-all is supported on the specified platform."""


# @hookspec
# def simple_deploy_get_automate_all_msg():
#     """Get a platform-specific message for confirming the --automate-all option."""


# @hookspec
# def simple_deploy_get_platform_name():
#     """Get the name of the platform that's being deployed to."""

@ hookspec
def simple_deploy_get_plugin_config():
    """Get plugin-specific attributes required by core."""

@hookspec
def simple_deploy_deploy(sd_config):
    """Carry out all platform-specific configuration and deployment work."""
