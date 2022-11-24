"""Defines the CLI for django-simple-deploy.
"""

class SimpleDeployCLI:

    def __init__(self, parser):
        """Defines the CLI for django-simple-deploy."""

        # Define groups of arguments.
        help_group = parser.add_argument_group("Get help")
        required_group = parser.add_argument_group("Required arguments")
        behavior_group = parser.add_argument_group("Customize simple_deploy's behavior")
        deployment_config_group = parser.add_argument_group("Customize deployment configuration")
        testing_group = parser.add_argument_group("Arguments for test runs")

        # Show our own help message.
        help_group.add_argument("--help", "-h", action="help", help="Show this help message and exit.")

        # It's tempting to add a `choices=['fly_io', 'platform_sh']` argument to
        #   this entry. But then we get a generic error message. We can write a 
        #   much better custom message to handle invalid --platform arguments.
        required_group.add_argument('--platform', '-p', type=str,
            help="Specifies the platform where the project will be deployed. Options: fly_io | platform_sh | heroku",
            default='')

        behavior_group.add_argument('--automate-all',
            help="Automates all aspects of deployment. Creates resources, makes commits, and runs `push` or `deploy` commands.",
            action='store_true')

        # Allow users to skip logging.
        behavior_group.add_argument('--no-logging',
            help="Do not create a log of the configuration and deployment process.",
            action='store_true')

        # Allow users to use simple_deploy even with an unclean git status.
        behavior_group.add_argument('--ignore-unclean-git',
            help="Run simple_deploy even with an unclean `git status` message.",
            action='store_true')

        # --- Platform.sh arguments ---

        # Allow users to set the deployed project name. This is the name that
        #   will be used by the platform, which may be different than the name
        #   used in the `startproject` command. See the Platform.sh script
        #   for use of this flag.
        deployment_config_group.add_argument('--deployed-project-name', type=str,
            help="Provide a name that the platform will use for this project.",
            default='')

        # Allow users to specify the region for a project when using --automate-all.
        deployment_config_group.add_argument('--region', type=str,
            help="Specify the region that this project will be deployed to.",
            default='us-3.platform.sh')

        # --- Developer arguments ---

        # If we're doing local unit testing, we need to avoid some network
        #   calls.
        testing_group.add_argument('--unit-testing',
            help="Used for local unit testing, to avoid network calls.",
            action='store_true')

        testing_group.add_argument('--integration-testing',
            help="Used for integration testing, to avoid confirmations.",
            action='store_true')