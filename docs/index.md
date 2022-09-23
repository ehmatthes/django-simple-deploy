# django-simple-deploy

Your first Django deployment should be simple. And your 100th, if it's a relatively simple site.

For selected platforms, `django-simple-deploy` allows you to make a live deployment in as little as three steps, with no manual configuration. Let `django-simple-deploy` configure your project, and then look to see what changes were made to support the deployment. Currently, three platforms have preliminary support: Fly.io, Platform.sh, and Heroku.

Automated approach
---

The `--automate-all` flag allows you to deploy a project in three steps. The only requirements are the following:
- You're using Git to track your project;
- Your project has a `requirements.txt` file;
- You have the Fly.io CLI installed;
- You've created an account on Fly.io and run `fly login`.

If you meet these requirements, here's what the deployment process looks like for Fly.io:

```
$ pip install django-simple-deploy
# Add simple_deploy to INSTALLED_APPS.
$ python manage.py simple_deploy --platform fly_io --automate-all
```

After taking these three steps, your project should appear in a new browser tab.

Configuration-only aproach
---

If you want more control over the deployment process, you can use the configuration-only mode:

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

This approach lets you see exactly what changes were made to your project in order to prepare for deployment. If you don't see any issues with these changes, you can commit the changes and use the platform's `push` or `deploy` command.