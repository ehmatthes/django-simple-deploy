django-simple-deploy
===

This app gives you a management command that configures your project for an initial deployment. It targets Heroku at the moment, but could be expanded to target other platforms as well.

If you have a relatively simple Django project that runs locally, you can deploy your project in a few short steps. The only change you'll need to make to your project is to add this app to `INSTALLED_APPS`.

Quick start
---

If you haven't already done so, install the [Heroku CLI](https://devcenter.heroku.com/articles/heroku-cli) and make sure you're using [Git](https://git-scm.com) to track your project.

Make sure your project is running in a virtual environment, and you have built a `requirements.txt` file with the command `pip freeze > requirements.txt`. (Other dependency management systems should be supported shortly.)

Then you can deploy your project using the following steps:

```
(venv)$ pip install django-simple-deploy
```

Now add `simple_deploy` to `INSTALLED_APPS`. The following commands will deploy your project:

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

Detailed instructions
---

Since this project only focuses on Heroku at the moment, you'll need to make a [Heroku](https://heroku.com/) account and install the [Heroku CLI](https://devcenter.heroku.com/articles/heroku-cli). Heroku lets you deploy up to five projects for free. Projects that are deployed on a free account "go to sleep" when they're not being used, but there is plenty of uptime to practice the deployment process before you need to pay for hosting.

Heroku uses Git to manage the deployment process, so you'll need to install and use [Git](https://git-scm.com) for version control if you're not already doing so. It's beyond the scope of these instructions to provide an introduction to Git, but if you're not using version control yet you really should run through a basic tutorial before focusing on deployment. It's also a good idea to commit all of your own changes before starting this deployment process. That way you can easily go back to your non-deployment state if anything goes wrong, and you can also easily see the changes that are made to prepare for deployment.

Each Django project quickly ends up with its own set of specific dependencies. These include a specific version of Django, and any number of other libraries that you end up using in a project. These need to be managed separate from any other Django project you might have on your system, and separate from any other Python project you work on. There are a number of approaches to dependency management. For the moment, this project assumes that you have a `requirements.txt` file that lists your project's depencies. If you're working in a virtual environment, you can generate this file with the command `pip freeze > requirements.txt`. Make sure you re-run this command any time you install a new package to your project.

For the deployment process, work in an active virtual environment in your project's root folder. You can install `django-simple-deploy` with Pip:

```
(venv)$ pip install django-simple-deploy
```

Now you'll need to add the app `simple_deploy` to `INSTALLED_APPS` in `settings.py`. This is a stripped-down app that makes a management command, `python manage.py simple_deploy`, available in your project.

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

Now your project should be ready for deployment. The remaining commands will push your project to Heroku, set up the database on Heroku, and open your project in a browser:

```
(venv)$ git push heroku main
(venv)$ heroku run python manage.py migrate
(venv)$ heroku open
```

Heroku assumes you are pushing your project from a `main` or `master` branch. If you are pushing from any other branch, you'll need to run a command like `git push heroku test_branch:main`. This pushes your test branch to Heroku's main branch. See the section "Deploying from a branch besides main" on Heroku's [Deploying with Git](https://devcenter.heroku.com/articles/git#deploying-code) page.

Ongoing development
---

After your initial deployment, you shouldn't need to run the `simple_deploy` command again. If you make changes to your project and want to push them to Heroku, take the following steps:

- Commit your changes locally.
- Run `git push heroku main`.
- If you made any changes to the database, run `heroku run python manage.py migrate`.

There's a lot more to know about deployement, so see the [Heroku Python documentation](https://devcenter.heroku.com/categories/python-support) and start to get familiar with the parts of it that are relevant to your project.

If it doesn't work
----

If anything doesn't work, this project will try to tell you what to do in order to deploy successfully. If it doesn't work and you think it should, feel free to [open an issue](https://github.com/ehmatthes/django-simple-deploy/issues). If the deployment fails and you want to undo all of these changes, you should be able to check out your last commit before starting this process and pick up your deployment efforts from there. You can also uninstall this package with the command `pip uninstall django-simple-deploy`. If you do this, make sure to remove `simple_deploy` from `INSTALLED_APPS`.

Contributing
---

If you want to contribute to this project, feel free to [open an issue](https://github.com/ehmatthes/django-simple-deploy/issues) and share how you'd like to help.







- Install the package `django-simple-deploy`.
- Add `simple_deploy` to `INSTALLED_APPS`.
- Run `heroku create`.
- Run `python manage.py simple_deploy`.
- Commit the new files and changes that `simple_deploy` makes.
- Run `git push heroku main`.
- Run `heroku run python manage.py migrate`.

That's it; your project should now be deployed and running on Heroku.