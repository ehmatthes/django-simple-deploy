---
title: "Quick Start: Deploying to Heroku"
hide:
    - footer
---

# Quick Start: Deploying to Heroku

## Overview

Heroku no longer has a free tier, but it's still a functioning hosting platform. As long as Heroku maintains a deployment process that can be scripted, `simple_deploy` will likely maintain support for Heroku.

Deployment to Heroku can be fully automated, but the configuration-only approach is recommended. This allows you to review the changes that are made to your project before committing them and making the initial push. The fully automated approach configures your project, commits these changes, and pushes the project to Heroku's servers.

## Prerequisites

Deployment to Heroku requires three things:

- You must be using Git to track your project.
- You need to have a `requirements.txt` file at the root of your project, or use Poetry or Pipenv to manage your project's dependencies.
- The [Heroku CLI](https://devcenter.heroku.com/articles/heroku-cli) must be installed on your system.

## Configuration-only deployment

First, install `django-simple-deploy`, and add `simple_deploy` to `INSTALLED_APPS` in *settings.py*:

```sh
$ pip install django-simple-deploy
# Add "simple_deploy" to INSTALLED_APPS in settings.py.
$ git commit -am "Added simple_deploy to INSTALLED_APPS."
```

Now create a new Heroku app and database using the CLI, and run `simple_deploy` to configure your app:

```sh
$ heroku create
$ heroku addons:create heroku-postgresql:mini
$ python manage.py simple_deploy --platform heroku
```

The `heroku create` command is required. If you skip the step to create a database, `simple_deploy` will make that call for you.

At this point, you should review the changes that were made to your project. Running `git status` will show you which files were modified, and which new files were created.

If you want to continue with the deployment process, commit these change, push your project to Heroku, and run migrations against the deployed project. When deployment is complete, use the `open` command to see the deployed version of your project:

```sh
$ git add .
$ git commit -m "Configured for deployment to Heroku."
$ git push heroku main
$ heroku run python manage.py migrate
$ heroku open
```

You can find a record of the deployment process in `simple_deploy_logs`. It contains most of the output you saw when running `simple_deploy`.

## Automated deployment

If you want, you can automate this entire process. This involves just three steps:

```sh
$ pip install django-simple-deploy
# Add `simple_deploy` to INSTALLED_APPS in settings.py.
$ python manage.py simple_deploy --platform heroku --automate-all
```

You should see a bunch of output as Heroku resources are created for you, your project is configured for deployment, and `simple_deploy` pushes your project to Heroku's servers. When everything's complete, your project should open in a new browser tab.

## Pushing further changes

After the initial deployment, you're almost certainly going to make further changes to your project. When you've updated your project and it works locally, you can commit these changes and push your project again, without using `simple_deploy`:

```sh
$ git status
$ git add .
$ git commit -m "Updated project."
$ git push heroku main
```

## Troubleshooting

If deployment does not work, please feel free to open an [issue](https://github.com/ehmatthes/django-simple-deploy/issues). Please share the OS you're  using locally, and the specific error message or unexpected behavior you saw. If the project you're deploying is hosted in a public repository, please share that as well.

Please remember that `django-simple-deploy` is in a preliminary state. That said, I'd love to know the specific issues people are running into so we can reach a 1.0 state in a reasonable time frame.
