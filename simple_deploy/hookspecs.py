import pluggy

hookspec = pluggy.HookspecMarker("simple_deploy")

@hookspec
def simple_deploy_deploy():
    """Carry out all platform-specific configuration and deployment work."""

@hookspec
def simple_deploy_get_automate_all_msg():
    """Get a platform-specific message for confirming the --automate-all option."""