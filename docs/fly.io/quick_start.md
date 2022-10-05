Quick Start: Deploying to Fly.io
===

## Overview

Support for Fly.io is in a very preliminary phase. For example, it will likely fail if you already have a Django project deployed on Fly.io. `django-simple-deploy` should only be used on test projects at this point.

Deployment to Fly.io can be fully automated, but it's recommended to use the configuration-only approach. This allows you to review the changes that are made to your project before committing them and making the initial push. The fully automated approach configures your project, commits these changes, and pushes the project to Fly.io's servers.

## Prerequisites

Deployment to Fly.io requires three things:

- You must be using Git to track your project.
- You need to have a `requirements.txt` file at the root of your project.
- The [Fly.io CLI](https://fly.io/docs/hands-on/install-flyctl/) must be installed on your system.

## Configuration-only deployment (recommended)

First, install `django-simple-deploy`:

```
$ pip install django-simple-deploy
```

Then, add `simple_deploy` to `INSTALLED_APPS` in *settings.py*.

Now create a new Fly.io app using the CLI:

```
$ fly apps create --generate-name
```

This will create an empty app on Fly.io.

Now run `simple_deploy`, targeting the Fly.io platform:

```
$ python manage.py simple_deploy --platform fly_io
```

`simple_deploy` will create a database and link it to this app, and configure your project so it can be deployed.

At this point, if you're new to using Fly.io, you should look at the changes that were made to your project. Running `git status` will show you which files were modified, and which files were created for a successful deployment. If you want to continue with the deployment process, commit these changes:

```
$ git status
$ git add .
$ git commit -m "Configured for deployment to Fly.io."
```

Now you're ready to deploy your project:

```
$ fly deploy
```

When this command completes, you're ready to view your project:

```
$ fly open
```

You can find a record of the deployment process in `simple_deploy_logs`. It contains most of the output you saw when running `simple_deploy`.

## Using `--automate-all`

If you want, you can automate this entire process. This involves just three steps:

```
$ pip install django-simple-deploy
# Add `simple_deploy` to INSTALLED_APPS in settings.py.
$ python manage.py simple_deploy --platform fly_io --automate-all
```

You should see a bunch of output as Fly.io resources are created for you, your project is configured for deployment, and `simple_deploy` pushes your project to Fly.io's servers. When everything's complete, your project should open in a new browser tab.

## Pushing further changes

After the initial deployment, you're almost certainly going to make further changes to your project. When you've updated your project and it works locally, you can commit these changes and push your project again, without using `simple_deploy`:

```
$ git status
$ git add .
$ git commit -m "Updated project."
$ fly deploy
```





