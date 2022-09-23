# django-simple-deploy

Deploy a Django project in three steps, to Fly.io, Platform.sh, or Heroku.

Example usage:

```
$ pip install django-simple-deploy
# Add simple_deploy to INSTALLED_APPS.
$ python manage.py simple_deploy --platform fly_io --automate-all
```

If you have the Fly.io CLI installed and you're logged in to the CLI, your project should appear in a new browser tab.