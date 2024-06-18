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


def get_org_names(output_str):
    """Get org names from output of `platform organization:list --yes --format csv`.

    Sample input:
        Name,Label,Owner email
        <org-name>,<org-label>,<org-owner@example.com>
        <org-name-2>,<org-label-2>,<org-owner-2@example.com>

    Returns:
        list: [str]
        None: If user has no organizations.
    """
    if "No organizations found." in output_str:
        return None

    lines = output_str.split("\n")[1:]
    return [line.split(",")[0] for line in lines if line]
