import pluggy

hookspec = pluggy.HookspecMarker("simple_deploy")

@hookspec
def simple_deploy_deploy():
    """Carry out all platform-specific configuration and deployment work."""