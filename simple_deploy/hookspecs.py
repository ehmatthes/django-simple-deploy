import pluggy

hookspec = pluggy.HookspecMarker("django-simple-deploy")

@hookspec
def deploy():
    """Carry out all platform-specific configuration and deployment work."""