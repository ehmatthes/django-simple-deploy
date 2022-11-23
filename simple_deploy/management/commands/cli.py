"""Defines the CLI for django-simple-deploy.
"""

class SimpleDeployCLI:

    def __init__(self, parser):
        """Defines the CLI for django-simple-deploy."""

        required_group = parser.add_argument_group('required')

        # It's tempting to add a `choices=['fly_io', 'platform_sh']` argument to
        #   this entry. But then we get a generic error message. We can write a 
        #   much better custom message to handle invalid --platform arguments.
        required_group.add_argument('--platform', '-p', type=str,
            help="Specifies the platform where the project will be deployed.",
            default='')

        parser.add_argument('--automate-all',
            help="Automate all aspects of deployment?",
            action='store_true')

        # Allow users to skip logging.
        parser.add_argument('--no-logging',
            help="Do you want a record of simple_deploy's output?",
            action='store_true')

        # Allow users to use simple_deploy even with an unclean git status.
        parser.add_argument('--ignore-unclean-git',
            help="Run simple_deploy even with an unclean `git status` message.",
            action='store_true')

        # --- Platform.sh arguments ---

        # Allow users to set the deployed project name. This is the name that
        #   will be used by the platform, which may be different than the name
        #   used in the `startproject` command. See the Platform.sh script
        #   for use of this flag.
        parser.add_argument('--deployed-project-name', type=str,
            help="What name should the platform use for this project?\n(This is normally discovered automatically through inspection.)",
            default='')

        # Allow users to specify the region for a project when using --automate-all.
        parser.add_argument('--region', type=str,
            help="Which region do you want to deploy to?",
            default='us-3.platform.sh')

        # --- Developer arguments ---

        # If we're doing local unit testing, we need to avoid some network
        #   calls.
        parser.add_argument('--unit-testing',
            help="Used for local unit testing, to avoid network calls.",
            action='store_true')

        parser.add_argument('--integration-testing',
            help="Used for integration testing, to avoid confirmations.",
            action='store_true')