django-simple-deploy
===

*Initial Django deployments made easy*

This app gives you a management command that configures your project for an initial deployment. It targets [Heroku](https://heroku.com) and [Platform.sh](https://platform.sh) at the moment, and can be expanded to target other platforms as well.

If you have a relatively simple Django project that runs locally, you can deploy your project in a few short steps. The only change you'll need to make to your project is to add this app to `INSTALLED_APPS`.

![Simplest example of how to use django-simple-deploy](https://raw.githubusercontent.com/ehmatthes/django-simple-deploy/main/assets/simplest_example.png)

By default, the above command will deploy your project to Heroku. You can use the `--platform` argument to deploy to Platform.sh instead:

```
$ python manage.py simple_deploy --automate-all --platform platform_sh
```

All output is captured and written to a log file stored in `simple_deploy_logs/`, which is placed at the project's root directory.

Table of Contents
---

- [Prerequisites](#prerequisites)
    - [Cloud platform account](#cloud-platform-account)
    - [Use Git](#use-git)
    - [Identify dependencies](#identify-dependencies)
- [Quick start: using `--automate-all` on Heroku](#quick-start-using---automate-all-on-heroku)
- [If it doesn't work](#if-it-doesnt-work)
- [Understanding costs](#understanding-costs)
- [Contributing](#contributing)
- [Good luck, and please be mindful](#good-luck-and-please-be-mindful)
- More about [Heroku deployments](docs/heroku_deployments.md)
- Additional [documentation](docs/)

Prerequisites
---

### Cloud platform account

If you haven't already done so, make an account on the platform you want to use, and install the appropriate CLI:

- For Heroku deployments, install the [Heroku CLI](https://devcenter.heroku.com/articles/heroku-cli).
- For Platform.sh deployments, install the [Platform.sh CLI](https://docs.platform.sh/development/cli.html).

### Use Git

Also, make sure you're using [Git](https://git-scm.com) to track your project. You should commit all changes to your project before running simple_deploy, so you can easily revert the changes that simple_deploy makes if you need to.

### Identify dependencies

Make sure your project is running in a virtual environment, and you have either:

- Built a `requirements.txt` file with the command `pip freeze > requirements.txt`;
- Or, used Poetry to manage your project's requirements using a `pyproject.toml` file;
- Or, used Pipenv to create a `Pipfile`.

Quick start: using `--automate-all` on Heroku
---

The `--automate-all` flag allows you to deploy your project in just three steps:
- Install `django-simple-deploy`:
    - With pip: `$ pip install django-simple-deploy`
    - With Poetry: `$ poetry add django-simple-deploy`
    - With Pipenv: `$ pipenv install django-simple-deploy`
- Add `simple_deploy` to `INSTALLED_APPS`.
- Run `simple_deploy`:
    - For a Heroku deployment: `python manage.py simple_deploy --automate-all`

This will take care of creating a new app, configuring your project for deployment, committing all changes, pushing the project to your platform's servers, running the initial migration, and opening the project in a new browser tab.

The default Heroku deployment should be free unless you already have more than the minimum allowed apps.

Read more about [Heroku deployments](docs/heroku_deployments.md), or see the [full set of CLI arguments](docs/cli_args.md).

If it doesn't work
----

If anything doesn't work, this project will try to tell you what to do in order to deploy successfully. If it doesn't work and you think it should, feel free to [open an issue](https://github.com/ehmatthes/django-simple-deploy/issues). If the deployment fails and you want to undo all of these changes, you should be able to check out your last commit before starting this process and pick up your deployment efforts from there. You can also uninstall this package with the command `pip uninstall django-simple-deploy`. If you do this, make sure to remove `simple_deploy` from `INSTALLED_APPS`.

If you've lost the terminal output after running `manage.py simple_deploy`, you can find the output in the `simple_deploy_logs/` directory. If you need to disable logging, you can use the `--no-logging` flag:

```
$ python manage.py simple_deploy --no-logging
```

Understanding costs
---

Every cloud provider charges something for a deployment that's expected to be available at all times, and that's a perfectly reasonable policy. Platforms should provide a free or low-cost option for people who are learning to make deployments. Each platform differs in how they approach offering this kind of support.

The django-simple-deploy project tries to use the lowest-cost option on each platform that's supported, but ultimately the cost of any deployment is entirely your responsibility. Whatever platform you choose, make sure you understand how to access the provider's dashboard, and be diligent about knowing your current and ongoing costs.

This project will make some references to specific plans and their costs, but those plans and costs can change at any time. Again, it is your responsiblity to verify anything you read here, and make sure you're not incurring more charges than you anticipated.

If you see anything here that is inaccurate, please [open an issue](https://github.com/ehmatthes/django-simple-deploy/issues).

Contributing
---

If you want to contribute to this project, feel free to [open an issue](https://github.com/ehmatthes/django-simple-deploy/issues) and share how you'd like to help.

You can also see the [contributing](docs/contributing.md) page. Here you'll see how to demo the project, how to run unit and integration tests, and how to set up a development environment for the project.

This project has adopted the [Contributor Covenant](https://www.contributor-covenant.org/version/2/1/code_of_conduct/) as a [Code of Conduct](docs/code_of_conduct.md).

Good luck, and please be mindful
---

Web apps have been around for a while now, and many people take them for granted because we've seen so many silly projects. But the power of a web app has never been diminished; if you have an idea for a project and you know how to build an app, you can share your idea with the world and see if it goes anywhere.

Every project that gains traction has an impact on people's lives. Many have unintended consequences, and some of that can not be avoided. If your project is gaining traction, please be mindful of the positive and negative impact it can have on people, and do what's needed to make sure it's a net positive in the world. :)
