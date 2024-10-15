class SDConfig:
    """Class for managing attributes of Command that need to be shared with plugins.
    """

    def __init__(self):
        """Define all attributes that will need to be shared."""
        # Aspects of user's system.
        self.on_windows = None

        # Aspects of user's local project.
        self.local_project_name = ""
        self.pkg_manager = ""

        # Paths in user's local project.
        self.project_root = None
        self.settings_path = None

        # Aspects of user's deployment.
        self.deployed_project_name = ""
        self.log_output = None
        self.automate_all = None

        # Attributes needed by plugin utility functions.
        self.use_shell = None
        self.e2e_testing = None
        self.unit_testing = None
        self.stdout = None
