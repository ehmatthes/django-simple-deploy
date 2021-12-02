django-simple-deploy
===

*Initial Django deployments made easy*

This app gives you a management command that configures your project for an initial deployment. It targets Heroku and Azure at the moment, and can be expanded to target other platforms as well.

If you have a relatively simple Django project that runs locally, you can deploy your project in a few short steps. The only change you'll need to make to your project is to add this app to `INSTALLED_APPS`.

![Simplest example of how to use django-simple-deploy](assets/simplest_example.png)

By default, the above command will deploy your project to Heroku. You can use the `--platform` argument to deploy to Azure instead:

```
$ python manage.py simple_deploy --automate-all --platform azure
```

Prerequisites
---

### Cloud platform account

If you haven't already done so, make an account on the platform you want to use, and install the appropriate CLI:

- For Heroku deployments, install the [Heroku CLI](https://devcenter.heroku.com/articles/heroku-cli).
- For Azure deployments, install the [Azure CLI](https://docs.microsoft.com/en-us/cli/azure/install-azure-cli).

### Use Git

Also, make sure you're using [Git](https://git-scm.com) to track your project.

### Identify dependencies

Make sure your project is running in a virtual environment, and you have either:

- Built a `requirements.txt` file with the command `pip freeze > requirements.txt`;
- Or, used Poetry to manage your project's requirements using a `pyproject.toml` file;
- Or, used Pipenv to create a `Pipfile`.

Quick start: using `--automate-all` on Heroku or Azure
---

The `--automate-all` flag allows you to deploy your project in just three steps:
- Install `django-simple-deploy`:
    - With pip: `$ pip install django-simple-deploy`
    - With Poetry: `$ poetry add django-simple-deploy`
    - With Pipenv: `$ pipenv install django-simple-deploy`
- Add `simple_deploy` to `INSTALLED_APPS`.
- Run `simple_deploy`:
    - For a Heroku deployment: `python manage.py simple_deploy --automate-all`
    - For an Azure deployment: `python manage.py simple_deploy --automate-all --platform azure`

This will take care of creating a new app, configuring your project for deployment, committing all changes, pushing the project to your platform's servers, running the initial migration, and opening the project in a new browser tab.

The default Heroku deployment should be free unless you already have more than the minimum allowed apps. The default Azure deployment uses a Postgres database that costs $0.034/hour ($24.82/month, as of 12/1/21).

Azure deployments can only be done with the `--automate-all` flag. If you don't automate everything, there's so much to do manually that it's not worth using `simple_deploy`.

Read more about [Heroku deployments](docs/heroku_deployments.md), or more about [Azure deployments]().

If it doesn't work
----

If anything doesn't work, this project will try to tell you what to do in order to deploy successfully. If it doesn't work and you think it should, feel free to [open an issue](https://github.com/ehmatthes/django-simple-deploy/issues). If the deployment fails and you want to undo all of these changes, you should be able to check out your last commit before starting this process and pick up your deployment efforts from there. You can also uninstall this package with the command `pip uninstall django-simple-deploy`. If you do this, make sure to remove `simple_deploy` from `INSTALLED_APPS`.

Contributing
---

If you want to contribute to this project, feel free to [open an issue](https://github.com/ehmatthes/django-simple-deploy/issues) and share how you'd like to help.

A great way to get started is to clone the project and run the integration tests. See the current [testing documentation](integration_tests/README.md) to get started.

Good luck, and please be mindful
---

Web apps have been around for a while now, and many people take them for granted because we've seen so many silly projects. But the power of a web app has never been diminished; if you have an idea for a project and you know how to build an app, you can share your idea with the world and see if it goes anywhere.

Every project that gains traction has an impact on people's lives. Many have unintended consequences, and some of that can not be avoided. If your project is gaining traction, please be mindful of the positive and negative impact it can have on people, and do what's needed to make sure it's a net positive in the world. :)
