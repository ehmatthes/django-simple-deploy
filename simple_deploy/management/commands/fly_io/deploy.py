"""Manages all Fly.io-specific aspects of the deployment process.

Notes:
- Internal references to Fly.io will almost always be flyio. Public references, such as
  the --platform argument, will be fly_io.
- self.deployed_project_name and self.app_name are identical. The first is used in the
  simple_deploy CLI, but Fly refers to "apps" in their docs. This redundancy makes it
  easier to code Fly CLI commands.
"""

import simple_deploy
from .platform_deployer import PlatformDeployer
from . import deploy_messages as platform_msgs


@simple_deploy.hookimpl
def simple_deploy_automate_all_supported():
    """Specify whether --automate-all is supported on the specified platform."""
    return True


@simple_deploy.hookimpl
def simple_deploy_get_automate_all_msg():
    """Get platform-specific confirmation message for --automate-all flag."""
    return platform_msgs.confirm_automate_all


@simple_deploy.hookimpl
def simple_deploy_deploy(sd):
    """Carry out platform-specific deployment steps."""
    platform_deployer = PlatformDeployer(sd)
    platform_deployer.deploy()
