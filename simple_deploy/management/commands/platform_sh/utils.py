"""Utilities specific to Platform.sh deployments."""


def get_project_name(output_str):
    """Get the project name from the output of `platform project:info`.

    Command is run with `--format csv` flag.

    Returns:
        str: project name
    """
    lines = output_str.splitlines()
    title_line = [line for line in lines if "title," in line][0]
    # Assume first project is one to use.
    project_name = title_line.split(",")[1].strip()

    return project_name


def get_org_name(output_str):
    """Get org name from output of `platfrom organizations:list`.

    Run with `--format csv` flag.

    Returns:
        str: org name
    """
    # Assume one org.
    target_line = output_str.split("\n")[1]
    org_name = target_line.split(",")[0].strip()

    return org_name
