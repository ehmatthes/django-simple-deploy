"""A collection of messages used in simple_deploy.py."""

# Module is called deploy_messages to avoid collisions with any messages.py 
#   files.
#
# Storing messages here makes for a much shorter simple_deploy.py file, and
#   makes it easier to see how the messages actually look on screen. The 
#   disadvantage is that it's harder to track what messages are being
#   displayed when working on simple_deploy.
# When you add a message here, make sure the stdout.write() call has a comment
#   that clearly summarizes what the message says.

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

cancel_automate_all = """
Okay, canceling this run. If you want to configure your project
for deployment, run simple_deploy again without the --automate-all flag.
"""

no_heroku_app_detected = """No Heroku app name has been detected.

- The simple_deploy command assumes you have already run 'heroku create'
  to start the deployment process.
- Please run 'heroku create', and then run
  'python manage.py simple_deploy' again.
- If you haven't already done so, you will need to install the Heroku CLI:
  https://devcenter.heroku.com/articles/heroku-cli
"""