class SDConfig:
    """Class for managing attributes of Command that need to be shared with plugins.
    """

    def __init__(self, stdout):
        """Define all attributes that will need to be shared."""
        # Aspects of user's system.
        self.on_windows = None
        self.on_macos = None

        # Aspects of user's local project.
        self.local_project_name = ""
        self.pkg_manager = ""
        self.requirements = None
        self.nested_project = None

        # Paths in user's local project.
        self.project_root = None
        self.git_path = None
        self.settings_path = None
        self.pipfile_path = None
        self.pyprojecttoml_path = None
        self.req_txt_path = None

        # Aspects of user's deployment.
        self.deployed_project_name = ""
        self.log_output = None
        self.automate_all = None
        self.region = None

        # Attributes needed by plugin utility functions.
        self.use_shell = None
        self.e2e_testing = None
        self.unit_testing = None
        self.stdout = stdout
