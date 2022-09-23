# django-simple-deploy

Your first Django deployment should be simple. And your 100th, if it's a relatively simple site.

For selected platforms, `django-simple-deploy` allows you to make a live deployment in as little as three steps, with no manual configuration. Let `django-simple-deploy` configure your project, and then look to see what changes were made to support the deployment. Currently, three platforms have preliminary support: Fly.io, Platform.sh, and Heroku.

Here's how it works for Fly.io:

```
$ pip install django-simple-deploy
# Add simple_deploy to INSTALLED_APPS.
$ python manage.py simple_deploy --platform fly_io --automate-all
```

The only assumptions are that you're using Git to track your project, you have a requirements.txt file, you have the Fly.io CLI installed, and you're logged in to the Fly.io CLI. After taking these three steps, your project should appear in a new browser tab.

This approach automates everything, including making commits for you after configuring your project. If you want more control, you can use the configuration-only mode:

```
$ fly apps create --generate-name
$ pip install django-simple-deploy
# Add simple_deploy to INSTALLED_APPS.
$ python manage.py simple_deploy --platform fly_io
$ git status                    # See what changes were made.
$ git add .
$ git commit -m "Configured for deployment."
$ fly deploy
$ fly open
```

This approach lets you see exactly what changes were made to your project in order to prepare for deployment.