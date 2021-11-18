"""A collection of messages used in deploy_heroku.py."""

# For conventions, see documentation in deploy_messages.py

from textwrap import dedent

from django.conf import settings


confirm_preliminary = """
***** Azure deployments are experimental at this point ***

- Support for deploying to Azure is in a preliminary phase at this point.
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

def success_msg(using_pipenv, heroku_app_name):
    """Success message, when not using --automate-all flag."""

    # You can't use backslashes in f-strings, so this is the cleanest way I
    #   can add a pipenv line when needed.
    newline = '\n'

    msg = dedent(f"""

        --- Your project is now configured for deployment on Heroku. ---
        
        To deploy your project, you will need to:
        - Commit the changes made in the configuration process.
        - Push the changes to Heroku.
        - Migrate the database on Heroku.
        
        The following commands should finish your initial deployment:{newline + '        $ pipenv lock' if using_pipenv else ''}
        $ git add .
        $ git commit -am "Configured for Heroku deployment."
        $ git push heroku main
        $ heroku run python manage.py migrate
        
        After this, you can see your project by running 'heroku open'.
        Or, you can visit https://{heroku_app_name}.herokuapp.com.

    """)
    return msg


def success_msg_automate_all(heroku_app_name, current_branch):
    """Success message, when using --automate-all."""

    # Set correct command for pushing to heroku.
    if current_branch in ('main', 'master'):
        push_command = f"$ git push heroku {current_branch}"
    else:
        push_command = f"$ git push heroku {current_branch}:main"

    msg = dedent(f"""

        --- Your project should now be deployed on Heroku. ---

        It should have opened up in a new browser tab.
        - If you see the message "There's nothing here, yet"
          try waiting a moment and then refreshing your browser.
        - Sometimes when the process is automated there's a little lag
          before the project is fully deployed.
        - You can also visit your project at {heroku_app_name}.herokuapp.com.

        If you make further changes and want to push them to Heroku,
        commit your changes and then run the following command:
        {push_command}

        Also, if you haven't already done so you should review the
        documentation for Python deployments on Heroku at:
        - https://devcenter.heroku.com/categories/python-support
        - This documentation will help you understand how to maintain
          your deployment.

    """)
    return msg