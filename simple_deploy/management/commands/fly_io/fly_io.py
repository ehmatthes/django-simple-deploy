import simple_deploy

@simple_deploy.hookimpl
def simple_deploy_get_automate_all_msg():
    print("*** generating automate all msg")
    return "Automate all msg fly_io"