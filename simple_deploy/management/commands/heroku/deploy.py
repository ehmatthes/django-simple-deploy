"""Manages all Heroku-specific aspects of the deployment process."""

import simple_deploy
from .platform_deployer import PlatformDeployer
from simple_deploy.management.commands.heroku import deploy_messages as platform_msgs


@simple_deploy.hookimpl
def simple_deploy_get_automate_all_msg():
    """Get platform-specific confirmation message for --automate-all flag."""
    return platform_msgs.confirm_automate_all

@simple_deploy.hookimpl
def simple_deploy_deploy(sd):
    """Carry out platform-specific deployment steps."""
    platform_deployer = PlatformDeployer(sd)
    platform_deployer.deploy()
