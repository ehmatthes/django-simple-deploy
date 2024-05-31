import pluggy

hookspec = pluggy.HookspecMarker("django-simple-deploy")

@hookspec
def deploy()