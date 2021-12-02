"""A collection of messages used in deploy_heroku.py."""

# For conventions, see documentation in deploy_messages.py

from textwrap import dedent

from django.conf import settings


require_automate_all = """

***** Azure deployments require the --automate-all flag. *****

- Support for deploying to Azure is in an exploratory phase at this point.
- Deploying to Azure without full atomation requires a significant number
  of steps, to the point where using simple_deploy doesn't help much.
- You would need to create a number of resources such as a database, and 
  then provide connection information for those resources. If you're comfortable
  doing these steps, you're not far off from doing a full deployment on your
  own using Azure.
- If you want to use simple_deploy with Azure, you can rerun this command with
  the `--automate-all` argument. You may also want to consider deploying to
  Heroku instead, which simple_deploy has better support for at this point.
"""

confirm_preliminary = """
***** Azure deployments are experimental at this point ***

- Support for deploying to Azure is in an exploratory phase at this point.
- You should only be using this project to deploy to Azure at this point if
  you are interested in helping to develop or test the simple_deploy project.
- You should look at the deploy_azure.py script before running this command,
  so you know exactly what Azure resources will be created on your account.
- You should understand the Azure portal, and be comfortable deleting resources
  that are created during this deployment, that you don't want persisting and
  accruing charges.
- You may want to cancel this run and deploy to Heroku instead. You can do this
  explicitly with the `--platform heroku` argument, or you can leave out the
  `--platform` argument and simple_deploy will deploy to Heroku by default.
"""

cancel_azure = """
Okay, cancelling Azure deployment.
"""

confirm_automate_all = """
***** The --automate-all flag means simple_deploy will: *****
- Modify your project so it's configured for deploying to Azure.
- Commit all changes to your project that are necessary for deployment.
  - These changes will be committed to the current branch, so you may want
    to make a new branch for this work.
- Do the following through your Azure account:
  - Add the db-up extension if it's not already installed.
  - Create a resource group called SimpleDeployGroup.
  - Create an appservice plan called SimpleDeployPlan.
  - Create a unique name for your app.
  - Create an Azure Database for PostgreSQL server and database.
  - Create a new app with the 'az webapp create' command. The app will be
    configured for Git deployments.
  - Set a number of environment variables to help manage your deployment.
  - Push your project to Azure.
  - Run the initial set of migrations to set up the remote database.
  - Open your deployed project in a new browser tab.
"""


# --- Dynamic strings ---
# These need to be generated in functions, to display information that's 
#   determined as the script runs.

def success_msg(using_pipenv, azure_app_name):
    """Success message, when not using --automate-all flag."""
    # DEV: Compose this message if we end up supporting a configuration-only
    #  deployment process for Azure.

    # You can't use backslashes in f-strings, so this is the cleanest way I
    #   can add a pipenv line when needed.
    newline = '\n'

    msg = dedent(f"""

    """)
    return msg


def success_msg_automate_all(azure_app_name, current_branch):
    """Success message, when using --automate-all."""

    # Set correct command for pushing to azure.
    push_command = f"$ git push azure {current_branch}:master"

    msg = dedent(f"""

        --- Your project should now be deployed on Azure. ---

        It should have opened up in a new browser tab.
        - If you see a generic Azure page, try waiting a moment and then
          refreshing your browser.
        - Sometimes when the process is automated there's a little lag
          before the project is fully deployed.
        - You can also visit your project at http://{azure_app_name}.azurewebsites.net.

        If you make further changes and want to push them to Azure,
        commit your changes and then run the following command:
        {push_command}

        *** Azure support is in an exploratory phase at this point. ***
        - The above command should push your changes to Azure, but you will 
          need to manually restart your server to use these changes.
        - You should be able to ssh into your server with the command:
            az webapp ssh --resource-group SimpleDeployGroup --name {azure_app_name}
          This should allow you to run management commands.
        - You should also be able to use a browser-based ssh session at:
            https://{azure_app_name}.scm.azurewebsites.net
        - If you know more about Azure deployments, please get in touch and help
          clean up the automated deployment process on Azure.
        - You should look at your Azure dashboard and make sure you understand what
          new resources were created, and how much they are costing. It's your
          responsibility to delete any resources you don't want, otherwise they
          will continue to accrue charges.        

    """)
    return msg