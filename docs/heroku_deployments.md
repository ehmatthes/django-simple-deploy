Heroku Deployments
===

This page discusses Heroku deployments in more detail. Before reading this page, make sure you've read the relevant parts of the [main readme file](../README.md). Use of the `--automate-all` flag is covered in the main readme.

Table of Contents
---

- [Configuration-only use](#configuration-only-use)
    - [Using requirements.txt, without --automate-all](#using-requirementstxt-without---automate-all)
    - [Using Poetry, without --automate-all](#using-poetry-without-automate-all)
    - [Using Pipenv, without --automate-all](#using-pipenv-without-automate-all)
- [Detailed description of configuration-only deployment](#detailed-description-of-configuration-only-deployment)    
- [Ongoing development](#ongoing-development)

Configuration-only use
---

If you don't use the `--automate-all` flag django-simple-deploy will configure your project, and leave you to review the changes, commit them, push the project to Heroku, and run the initial migration. You will also need to run `heroku create` before running simple_deploy. These steps should be straightforward, and can all be done from the command line as shown below.

### Using `requirements.txt`, without `--automate-all`

If you've met the prerequisites, you can deploy your project using the following steps:

```
(venv)$ pip install django-simple-deploy
```

Now add `simple_deploy` to `INSTALLED_APPS`.

The following commands will deploy your project:

```
(venv)$ heroku create
(venv)$ python manage.py simple_deploy
(venv)$ git status                               # See what changes were made.
(venv)$ git add .
(venv)$ git commit -am "Configured project for deployment."
(venv)$ git push heroku main
(venv)$ heroku run python manage.py migrate
(venv)$ heroku open
```

After running this last command, you should see your project open in a browser. :)

### Using Poetry, without `--automate-all`

If you've met the prerequisites, you can deploy your project using the following steps:

```
(venv)$ poetry add django-simple-deploy
```

Now add `simple_deploy` to `INSTALLED_APPS`.

The following commands will deploy your project:

```
(venv)$ heroku create
(venv)$ python manage.py simple_deploy
(venv)$ git status                               # See what changes were made.
(venv)$ git add .
(venv)$ git commit -am "Configured project for deployment."
(venv)$ git push heroku main
(venv)$ heroku run python manage.py migrate
(venv)$ heroku open
```

After running this last command, you should see your project open in a browser. :)

### Using Pipenv, without `automate-all`

If you've met the prerequisites, you can deploy your project using the following steps:

```
(venv)$ pipenv install django-simple-deploy
```

Now add `simple_deploy` to `INSTALLED_APPS`.

The following commands will deploy your project:

```
(venv)$ heroku create
(venv)$ python manage.py simple_deploy
(venv)$ git status                               # See what changes were made.
(venv)$ pipenv lock                              # Update new dependencies.
(venv)$ git add .
(venv)$ git commit -am "Configured project for deployment."
(venv)$ git push heroku main
(venv)$ heroku run python manage.py migrate
(venv)$ heroku open
```

After running this last command, you should see your project open in a browser. :)

Detailed description of configuration-only deployment
---

To deploy your project to Heroku, you'll need to make a [Heroku](https://heroku.com/) account and install the [Heroku CLI](https://devcenter.heroku.com/articles/heroku-cli). Heroku lets you deploy up to five projects for free. Projects that are deployed on a free account "go to sleep" when they're not being used, but there's plenty of uptime to practice the deployment process before you need to pay for hosting.

Heroku uses Git to manage the deployment process, so you'll need to install and use [Git](https://git-scm.com) for version control if you're not already doing so. It's beyond the scope of these instructions to provide an introduction to Git, but if you're not using version control yet you really should run through a basic tutorial before focusing on deployment. It's also a good idea to commit all of your own changes before starting this deployment process. That way you can easily go back to your non-deployment state if anything goes wrong, and you can also see the specific changes that are made in preparing for deployment.

Each Django project quickly ends up with its own set of specific dependencies. These include a specific version of Django, and any number of other libraries that you end up using in a project. These dependencies need to be managed separate from any other Django project you might have on your system, and separate from any other Python project you work on. There are a number of approaches to dependency management. If you're working in a virtual environment, you can generate a requirements file with the command `pip freeze > requirements.txt`. If you're using Poetry, a `pyproject.toml` file and a `poetry.lock` file were probably generated when you installed your dependencies. If you're using Pipenv, a `Pipfile` and `Pipfile.lock` were probably generated when you installed your dependencies.

For the deployment process, work in an active virtual environment in your project's root folder. You can install `django-simple-deploy` with Pip:

```
(venv)$ pip install django-simple-deploy
```

You can also install it with Poetry:

```
(venv)$ poetry add django-simple-deploy
```

You can also install it with Pipenv:

```
(venv)$ pipenv install django-simple-deploy
```

You'll need to add the app `simple_deploy` to `INSTALLED_APPS` in `settings.py`. This is a stripped-down app that makes the management command `manage.py simple_deploy` available in your project.

Now run:

```
(venv)$ heroku create
```

This creates an app for you on the Heroku platform. You'll get a URL for your project, such as `salty-river-90253.herokuapp.com`. Heroku will also establish a connection between your local project and the Heroku app.

The following commands will configure your project for deployment to Heroku. It's a good idea to run `git status` after configuring for deployment, so you can review the changes that were made to your project in preparing for deployment.

```
(venv)$ python manage.py simple_deploy
(venv)$ git status
(venv)$ git add .
(venv)$ git commit -am "Configured project for deployment."
```

If you're using Poetry, `manage.py simple_deploy` will generate a `requirements.txt` file for you, without affecting your local environment. It does this because Heroku doesn't recognize `pyproject.toml` or `poetry.lock`.

If you're using Pipenv, you'll need to regenerate your lock file after running `manage.py simple_deploy`. The `simple_deploy` command modifies your Pipfile, and if you try to push your project to Heroku without rebuilding the lock file it will complain about an out-of-date lock file. Your commands will look like this:

```
(venv)$ python manage.py simple_deploy
(venv)$ git status
(venv)$ pipenv lock
(venv)$ git add .
(venv)$ git commit -am "Configured project for deployment."
```

Now your project should be ready for deployment. To configure your project, `simple_deploy` does the following:

- Sets an environment variable on the Heroku server called `ON_HEROKU`, that lets the project detect when it's being run on the Heroku server. This allows us to have a section in `settings.py` that only applies to the deployed version of the project.
- Adds `django-simple-deploy` to your requirements file, if it's not already there.
- Generates a `Procfile`, telling Heroku what process to run. This is the production version of `manage.py runserver`.
- Adds `gunicorn`, `dj-database-url`, `psycopg2`, and `whitenoise` to your requirements file, if they're not already listed. These packages help serve the project in production, including managing the production database and serving static files efficiently.
- Makes sure the `ALLOWED_HOSTS` setting includes the URL that Heroku created for the project.
- Modifies `settings.py` to use the production database.
- Configures the project to use `whitenoise` to manage static files such as CSS and JavaScript files.

If you want to see the changes that were made, run `git status` and take a look at the files that were created or modified after running `manage.py simple_deploy`. Also, if you're curious to see the code that generates these changes, you can see the `simple_deploy.py` code [here](https://github.com/ehmatthes/django-simple-deploy/blob/main/simple_deploy/management/commands/simple_deploy.py).

The remaining commands will push your project to Heroku, set up the database on Heroku, and open your project in a browser:

```
(venv)$ git push heroku main
(venv)$ heroku run python manage.py migrate
(venv)$ heroku open
```

Heroku assumes you are pushing your project from a `main` or `master` branch. If you're pushing from any other branch, you'll need to run a command like `git push heroku test_branch:main`. This pushes your test branch to Heroku's main branch. See the section "Deploying from a branch besides main" on Heroku's [Deploying with Git](https://devcenter.heroku.com/articles/git#deploying-code) page.

Ongoing development
---

After your initial deployment, you shouldn't need to run the `simple_deploy` command again. If you make changes to your project and want to push them to Heroku, take the following steps:

- Commit your changes locally.
- Run `git push heroku main`.
- If you made any changes to the database, run `heroku run python manage.py migrate`.

There's a lot more to know about deployement, so see the [Heroku Python documentation](https://devcenter.heroku.com/categories/python-support) and start to get familiar with the parts of it that are relevant to your project.

