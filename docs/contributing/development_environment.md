---
title: "Setting Up a Development Environment"
hide:
    - footer
---

# Setting Up a Development Environment

Setting up a development environment will let you make changes to the `simple_deploy` project, and deploy test projects using your version of `simple_deploy`. If your work improves the project, you can make a Pull Request and we'll review your changes to see if they're ready to be merged into the main project.

If you are doing any significant work, please open an issue and communicate with the rest of the team first. This project is evolving rapidly, and we don't want to see people do a bunch of work that conflicts with other work that's being done, and can't end up being merged to the main project.

## Make a local working copy of the project

First, fork the `django-simple-deploy` project on GitHub. If you haven't done this before, look for the Fork button in the upper right corner of the project's [home page](https://github.com/ehmatthes/django-simple-deploy/). This will copy the main branch of the project to a new repo under your account.

Next, clone this repository to your local system and install the necessary dependencies:

=== "macOS/Linux"

    ```
    $ git clone https://github.com/YOUR_GITHUB_USERNAME/django-simple-deploy.git
    $ cd django-simple-deploy
    $ python3 -m venv dsd_env
    $ source dsd_env/bin/activate
    $ pip install --upgrade pip
    $ pip install -r requirements.txt
    ```

=== "Windows"

    ```
    > git clone https://github.com/YOUR_GITHUB_USERNAME/django-simple-deploy.git
    > cd django-simple-deploy
    > python -m venv dsd_env
    > dsd_env\Scripts\activate
    > pip install --upgrade pip
    > pip install -r requirements.txt
    ```


## Make a test project to run `simple_deploy` against

In order to work on `django-simple-deploy`, you need a Django project outside the main project directory to run the `simple_deploy` command against. You can either copy a project from the `sample_project/` directory, or clone the [standalone sample project](https://github.com/ehmatthes/dsd_sample_blog_reqtxt).

### Copy a project from `sample_project/`

The projects in `sample_project` contain multiple dependency management files. No real-world Django project would have this combination of files; it's set up this way to support automated testing of multiple dependency management systems. During testing, the unneeded files are removed so that the target dependency management system can be tested.

If you're going to copy a project from this directory, start by copying the entire project, such as `blog_project/`, to a directory outside the `django-simple-deploy/` directory. Then choose a dependency management system: bare `requirements.txt` file, Poetry, or Pipenv. Remove the files not needed for the dependency management system.

=== "Bare requirements.txt file"

    Remove `Pipfile` and `pyproject.toml`.

=== "Poetry"

    Remove `requirements.txt` and `Pipfile`.

=== "Pipenv"

    Remove `requirements.txt` and `pyproject.toml`.

### Copy the standalone test project

The [standalone test project](https://github.com/ehmatthes/dsd_sample_blog_reqtxt) is maintained to make it easier for people to [document a test run](http://localhost:8000/contributing/test_run/). You are welcome to use this project when working on `simple_deploy`.

Clone the test repo to a directory outside of the `django-simple-deploy/` directory:

```
$ git clone https://github.com/ehmatthes/dsd_sample_blog_reqtxt.git
```

## Make sure the test project works

The core idea of `django-simple-deploy` is that if you have a simple but nontrivial Django project that works locally, we can help you deploy it to a supported platform. Let's make sure the project works locally before trying to deploy it. The following instructions work with a `requirements.txt` file; you'll follow a similar process for other dependency management systems such as Poetry or Pipenv.

In the root directory of the test project, build out the environment and start the development server:

=== "macOS/Linux"

    ```
    $ python3 -m venv b_env
    $ source b_env/bin/activate
    $ pip install --upgrade pip
    $ pip install -r requiremnents.txt
    $ python manage.py migrate
    $ python manage.py runserver
    ```

=== "Windows"

    ```
    > python -m venv b_env
    > b_env\Scripts\activate
    > pip install --upgrade pip
    > pip install -r requiremnents.txt
    > python manage.py migrate
    > python manage.py runserver
    ```

Open a new terminal tab and run the functionality tests against the local project:

=== "macOS/Linux"

    ```
    $ source b_env/bin/activate
    $ python test_deployed_app_functionality.py --url http://localhost:8000
    ```

    The tests expect an empty database to start. If you've already entered sample data, run the tests with the `--flush-db` flag:

    ```
    $ python test_deployed_app_functionality.py --flush-db --url http://localhost:8000
    ```

=== "Windows"

    ```
    > b_env\Scripts\activate
    > python test_deployed_app_functionality.py --url http://localhost:8000
    ```

    The tests expect an empty database to start. If you've already entered sample data, run the tests with the `--flush-db` flag:

    ```
    > python test_deployed_app_functionality.py --flush-db --url http://localhost:8000
    ```

If the tests pass, you're ready to run a deployment using your local version of `django-simple-deploy`.

## Make a new commit

Before you run `simple_deploy`, make a commit so you can more easily do repeated deployments without having to build the test project from scratch:

```
$ git add .
$ git commit -am "Initial state, before using simple_deploy."
```

## Run `simple_deploy` locally

To use your local version of `django-simple-deploy`, we'll install `simple_deploy` using an [editable install](https://pip.pypa.io/en/stable/topics/local-project-installs/#editable-installs). Normally `pip install` copies a package's files to your environment. Changes to the source files aren't copied to your environment until you upgrade or reinstall the package. With an editable install, pip instead sets up the project so the package is imported into the environment each time it's used. This means you can make changes in your `django-simple-deploy/` directory, and those changes will be used in your test project the next time you run `simple_deploy`.

We'll make an editable installation of `django-simple-deploy`, and then use the current local version of the project to run a test deployment of the sample project.

```
$ python -m pip install -e /local/path/to/django-simple-deploy/
```

Now, visit the [Quick Start](../quick_starts/index.md) page for the platform you want to target, and follow the directions you see there. Make sure you skip the `pip install django-simple-deploy` step, because we've already made the editable install of this package.

## Test the deployment

To make sure the deployment worked, run the functionality tests against the deployed version of the sample project:

```
$ python test_deployed_app_functionality.py --url https://deployed-project-url
```

Keep in mind that the `--flush-db` command will not work on a deployed project. Also, note that these automated tests don't always work on projects that are deployed using the lowest-tier resources on the target platform. If you see the deployed site in the browser but the tests fail, try clicking through different pages and making a user account. It's possible that the project works for manual use, but doesn't respond well to rapid automated test requests.





---

- then pip install -e
- add simple_deploy to installed_apps
- make a commit
- hack
- run your deployment work
- you can use `manage.py simple_deploy --unit-testing` to see configuration changes, without making a deployment
- reset --hard commit_hash to undo config changes
- make sure git status, and delete anything that didn't get reset, ie simple_deploy_logs/
- Update tests