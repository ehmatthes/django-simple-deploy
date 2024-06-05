import pluggy

hookspec = pluggy.HookspecMarker("simple_deploy")

@hookspec
def check_reference_file():
    """Compare a file against a reference file."""