---
title: "Setting Up a Development Environment"
hide:
    - footer
---

# Setting Up a Development Environment

Setting up a development environment will let you make changes to the `simple_deploy` project, and deploy test projects using your version of `simple_deploy`. If your work improves the project, you can make a Pull Request and we'll review your changes to see if they're ready to be merged into the main project.

If you are doing any significant work, please open an issue and communicate with the rest of the team first. This project is evolving rapidly, and we don't want to see people do a bunch of work that conflicts with other work that's being done, and can't end up being merged to the main project.

Also, if you haven't done so already, please review the [Testing on Your Own Account](own_account.md) page before moving forward.

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

## Make an editable install of `django-simple-deploy`

To use your local version of `django-simple-deploy`, we'll install `simple_deploy` using an [editable install](https://pip.pypa.io/en/stable/topics/local-project-installs/#editable-installs). Normally `pip install` copies a package's files to your environment. Changes to the source files aren't copied to your environment until you upgrade or reinstall the package. With an editable install, pip instead sets up the project so the package is imported into the environment each time it's used. This means you can make changes in your `django-simple-deploy/` directory, and those changes will be used in your test project the next time you run `simple_deploy`.

Here's how to make the editable install:

```
$ python -m pip install -e /local/path/to/django-simple-deploy/
```

## Run `simple_deploy` against the test project

Now, visit the [Quick Start](../quick_starts/index.md) page for the platform you want to target, and follow the directions you see there. Make sure you skip the `pip install django-simple-deploy` step, because we've already made the editable install of this package.

### Test the deployment

To make sure the deployment worked, run the functionality tests against the deployed version of the sample project:

```
$ python test_deployed_app_functionality.py --url https://deployed-project-url
```

Keep in mind that the `--flush-db` command will not work on a deployed project. Also, note that these automated tests don't always work on projects that are deployed using the lowest-tier resources on the target platform. If you see the deployed site in the browser but the tests fail, try clicking through different pages and making a user account. It's possible that the project works for manual use, but doesn't respond well to rapid automated test requests.

### Destroy the remote resources

At this point, you can destroy the remote resources that were created. Remote resources should be destroyed automatically when running integration tests, but they are not destroyed for you when testing in the manner we've just run through. If you have any questions about this, see the [Testing on Your Own Account](own_account.md) page.

### Reset the test project

After verifying that your local version of `django-simple-deploy` works when run against the test project, you'll need to reset the test project. This will let you modify `django-simple-deploy`, and then run `simple_deploy` again and see the effect of your changes.

To reset the project, run `git reset --hard commit_hash`, using the hash of the commit that you made after making sure the test project works locally. Also, run `git status` and make sure you remove any files or directories that are left in the project, such as `simple_deploy_logs/`. The `.platform/` directory also tends to hang around after resetting the test project, when testing against Platform.sh.

## Developing `simple_deploy`

Now you're ready to do your own development work on `simple_deploy`. Make a new branch on your fork of the project, and make any changes you want to the codebase. When you want to see if your changes improve the configuration and deployment process, go back to the [Run `simple_deploy` locally](#run-simple_deploy-against-the-test-project) section and repeat those steps.

### Helpful flags for development work

The `--unit-testing` and `--ignore-unclean-git` flags can be really helpful when doing development work. For example say you're revising the approach to generating a dockerfile for Poetry users when deploying to Fly.io. You've modified some of the project's code, and you want to see how it impacts your demo project. Run the following command:

```
$ python manage.py simple_deploy --platform fly_io --unit-testing
```

This won't run the unit tests, but it will skip the same network calls that are skipped during unit testing. You should see most of the same configuration that's done during a normal run, using sample resource names.

When you've made more changes and want to run `simple_deploy` again, but all you're interested in is the Dockerfile that's generated, run the following two commands:

```
$ rm Dockerfile
$ python manage.py simple_deploy --platform fly_io --unit-testing --ignore-unclean-git
```

This will avoid network calls and use sample resource names again, and it will ignore the fact that you have significant uncommitted changes. A new Dockerfile should be generated, and you can repeat these steps to rapidly develop the code that generates the Dockerfile.

## Making a PR

When this project is more mature, there will be a clear routine for running tests before opening a new PR. But testing this project is not straightforward. For example, there's no need to run a full test suite making multiple full deployments for every possible PR. If you're satisfied with your work and think it should be merged into the main project, feel free to open a PR.

## Running unit tests

Restructuring the unit tests is one of the higher-priority issues. When that work is being done, documentation for unit tests will be moved to the official documentation. For now, if you're interested in running the unit tests, see the [old documentation for unit tests](https://github.com/ehmatthes/django-simple-deploy/blob/main/old_docs/unit_tests.md).

## Running integration tests

The integration tests have been critical in developing the project to this point. That said, they are in need of restructuring as well. If you want to understand the current state of the integration tests, see the [old documentation](https://github.com/ehmatthes/django-simple-deploy/blob/main/old_docs/integration_tests.md) as well.

## Closing thoughts

This is a rapidly evolving project. Please feel free to open an [issue](https://github.com/ehmatthes/django-simple-deploy/issues/new/choose) or a [discussion](https://github.com/ehmatthes/django-simple-deploy/discussions/new) about any aspect of this project.