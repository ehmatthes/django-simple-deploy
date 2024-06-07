"""Manages all platform.sh-specific aspects of the deployment process."""

# Note: All public-facing references to platform.sh will include a dot, dash, or
#  underscore, ie platform_sh.
#  Internally, we won't use a space, ie platformsh or plsh.

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
