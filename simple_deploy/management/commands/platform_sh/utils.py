"""Utilities specific to Platform.sh deployments."""

def get_project_name(output_str):
    """Get the project name from the output of `platform project:info`.

    Command is run with --format csv flag.

    Returns:
        str: project name
    """
    lines = output_str.splitlines()
    title_line = [line for line in lines if "title," in line][0]
    # Assume first project is one to use.
    return title_line.split(",")[1].strip()