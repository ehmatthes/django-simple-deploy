Platform.sh Deployments
===

This page discusses Platform.sh deployments in more detail. Before reading this page, make sure you've read the relevant parts of the [main readme file](../README.md). 

Table of Contents
---

- [Configuration-only use](#configuration-only-use)
    - [Using requirements.txt](#using-requirementstxt)
- [Detailed description of configuration-only deployment](#detailed-description-of-configuration-only-deployment)    
- [Ongoing development](#ongoing-development)

Configuration-only use
---

django-simple-deploy will configure your project, and leave you to review the changes, commit them, and push the project to Platform.sh. These steps should be straightforward, and can all be done from the command line as shown below.

### Using `requirements.txt`

If you've met the prerequisites, you can deploy your project using the following steps:

```
(venv)$ pip install django-simple-deploy
```

Now add `simple_deploy` to `INSTALLED_APPS`.

The following commands will deploy your project:

```
(venv)$ platform create
(venv)$ python manage.py simple_deploy --platform platform_sh
(venv)$ git status                               # See what changes were made.
(venv)$ git add .
(venv)$ git commit -am "Configured project for deployment."
(venv)$ platform push
(venv)$ platform url
```

After running this last command, you should see your project open in a browser. :)

Detailed description of configuration-only deployment
---

To deploy your project to Platform.sh, you'll need to make a [Platform.sh](https://platform.sh/) account and install the [Platform.sh CLI](https://docs.platform.sh/development/cli.html). Platform.sh lets you deploy up to two projects per day for free; I'm not sure how many projects you can have in total. I believe there's also a time limit for the free trial.

You'll need to install and use [Git](https://git-scm.com) for version control if you're not already doing so. It's beyond the scope of these instructions to provide an introduction to Git, but if you're not using version control yet you really should run through a basic tutorial before focusing on deployment. It's also a good idea to commit all of your own changes before starting this deployment process. That way you can easily go back to your pre-deployment state if anything goes wrong, and you can also see the specific changes that are made in preparing for deployment. If you haven't committed all of your changes before running `simple_deploy`, you'll see a warning to do so. You can override this with the `--ignore-unclean-git` flag if you have a specific reason to do so.

Each Django project quickly ends up with its own set of specific dependencies. These include a specific version of Django, and any number of other libraries that you end up using in a project. These dependencies need to be managed separate from any other Django project you might have on your system, and separate from any other Python project you work on. There are a number of approaches to dependency management. If you're working in a virtual environment, you can generate a requirements file with the command `pip freeze > requirements.txt`.

For the deployment process, work in an active virtual environment in your project's root folder. 

First, install `platformshconfig`. This package is used to determine whether local settings or Platform.sh-specific settings should be used:

```
(venv)$ pip install platformshconfig
```

You can install `django-simple-deploy` with pip:

```
(venv)$ pip install django-simple-deploy
```

You'll need to add the app `simple_deploy` to `INSTALLED_APPS` in `settings.py`. This is a stripped-down app that makes the management command `manage.py simple_deploy` available in your project.

The following commands will create an empty project on Platform.sh, and configure your project for deployment. It's a good idea to run `git status` after configuring for deployment, so you can review the changes that were made to your project in preparing for deployment.

```
(venv)$ platform create
(venv)$ python manage.py simple_deploy
(venv)$ git status
(venv)$ git add .
(venv)$ git commit -am "Configured project for deployment."
```

[Update regarding Poetry]

[Update regarding Pipenv]

Now your project should be ready for deployment. To configure your project, `simple_deploy` does the following:

- Adds a Platform.sh-specific block of settings at the end of `settings.py`. This modifies settings for `ALLOWED_HOSTS`, `DEBUG`, static files settings, the `SECRET_KEY` setting, and the database settings.
- Adds Platform.sh-specific configuration files: `.platform.app.yaml` and `.platform/services.yaml`.
- Adds required packages, by writing a `requirements_remote.txt` file.
    - The Platform.sh deployment process allows for multiple requirements files to be specified, which makes it easy to specify additional remote-only packages. The `platformshconfig` package is added to the core requirements file because it's used locally in `settings.py`. The two packages `gunicorn` and `psycopg2` are added to the `requirements_remote.txt` file.

If you want to see the changes that were made, run `git status` and take a look at the files that were created or modified after running `manage.py simple_deploy`. Also, if you're curious to see the code that generates these changes, you can see the `simple_deploy.py` code [here](https://github.com/ehmatthes/django-simple-deploy/blob/main/simple_deploy/management/commands/simple_deploy.py); the Platform.sh-specific script is [here](https://github.com/ehmatthes/django-simple-deploy/blob/main/simple_deploy/management/commands/utils/deploy_platformsh.py).

Then push your project, and open the deployed project in a browser:

```
(venv)$ platform push
(venv)$ platform url
```

You should see your live project open in a new browser tab.

Ongoing development
---

After your initial deployment, you shouldn't need to run the `simple_deploy` command again. If you make changes to your project and want to push them to Platform.sh, take the following steps:

- Commit your changes locally.
- Run `platform push`.

There's a lot more to know about deployement, so see the [Platform.sh documentation](https://docs.platform.sh) and start to get familiar with the parts of it that are relevant to your project. The main Python page is [here](https://docs.platform.sh/languages/python.html), and you can see an example Django project configured for deployment [here](https://github.com/platformsh-templates/django4).

Deleting the project
---

If you are just testing the deployment process and you want to destroy the project, you can do so with the `platform project:delete` command. You should verify that this command was successful, and that you will not continue to accrue charges. You may want to visit the Platform.sh online console and verify that this project no longer exists in your dashboard.

