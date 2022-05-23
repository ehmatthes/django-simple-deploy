"""A collection of messages used in deploy_heroku.py."""

# For conventions, see documentation in deploy_messages.py

from textwrap import dedent

from django.conf import settings


confirm_preliminary = """
***** Deployments to platform.sh are experimental at this point ***

- Support for deploying to platform.sh is in an exploratory phase at this point.
- You should only be using this project to deploy to platform.sh at this point if
  you are interested in helping to develop or test the simple_deploy project.
- You should look at the deploy_platformsh.py script before running this command,
  so you know what kinds of changes will be made to your project.
- You should understand the platform.sh console, and be comfortable deleting resources
  that are created during this deployment.
- You may want to cancel this run and deploy to Heroku instead. You can do this
  explicitly with the `--platform heroku` argument, or you can leave out the
  `--platform` argument and simple_deploy will deploy to Heroku by default.
"""

cancel_plsh = """
Okay, cancelling platform.sh deployment.
"""






confirm_automate_all = """
The --automate-all flag means simple_deploy will:
- Run `heroku create` for you, to create a new Heroku project.
- Commit all changes to your project that are necessary for deployment.
  - These changes will be committed to the current branch, so you may want
    to make a new branch for this work.
- Push these changes to Heroku.
- Run the initial set of migrations to set up the remote database.
- Open your deployed project in a new browser tab.
"""

no_heroku_app_detected = """No Heroku app name has been detected.

- The simple_deploy command assumes you have already run 'heroku create'
  to start the deployment process.
- Please run 'heroku create', and then run
  'python manage.py simple_deploy' again.
- If you haven't already done so, you will need to install the Heroku CLI:
  https://devcenter.heroku.com/articles/heroku-cli
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