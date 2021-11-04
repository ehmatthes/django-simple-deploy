"""A collection of messages used in simple_deploy.py."""

# Module is called deploy_messages to avoid collisions with any messages.py 
#   files.

confirm_automate_all = """
The --automate-all flag means simple_deploy will:
- Run `heroku create` for you, to create a new Heroku project;
- Commit all changes to your project that are necessary for deployment;
  These changes will be committed to the current branch, you
    may want to make a new branch for this work.
- Push these changes to Heroku;
- Run `heroku migrate` to set up the remote database;
- Call `heroku open` to open your deployed project in a new browser tab.
"""

cancel_automate_all = """
Okay, canceling this run. If you want to configure your project
  for deployment, run simple_deploy again without the --automate-all flag.
"""