---
title: "Documenting a Test Run"
hide:
    - footer
---

# Documenting a Test Run

One of the simplest ways to start contributing is to document a test run of the project. In this early pre-1.0 phase of development, every test run is a helpful data point.

## Minimum Requirements

Before jumping in, you should be clear about one aspect of working on `django-simple-deploy`. There's really no way to contribute to the project without an active account on one of the platforms that `simple_deploy` supports. Make sure you read the [testing on your own account](own_account.md) page before continuing.

The following directions are written with a focus on Fly.io, but can be adapted to any platform that's currently supported by `simple_deploy`.

## Configuration and `--automate-all` Modes

The recommended usage for `simple_deploy` is a "configuration-only" mode. With this usage, you create a new project on the chosen platform, and then run `simple_deploy`, which configures your project for deployment to the targeted platform. You then review and commit changes, and run your platform's `push` or `deploy` command. Using the configuration mode will give you a better sense of what the automated mode does for users.

There is an option to have `simple_deploy` automate every step of this process. Please feel free to test this usage as well.

Both approaches require an actual deployment, because `simple_deploy` can not configure a local project for deployment without a specific app to target. For example, creating an app often creates a remote project, database, and some config settings. `simple_deploy` needs to inspect the local project, and query the remote project in order to complete configuration.

## Brief Description

For a test run, feel free to try `simple_deploy` against the provided sample project, or against a project of your own. The sample project is a blog-making platform, which includes user accounts, meaningful use of a database, and Bootstrap styling. If you're testing against your own project, it's really helpful if your project is publicly accessible. If not, we can't really do much with any error reports that your test run generates.

Here are the overall steps you'll take:

- Open an issue using the [Documenting a Test Run](https://github.com/ehmatthes/django-simple-deploy/issues/new?assignees=&labels=&template=documenting-a-test-run.md&title=Documenting+a+Test+Run) issue template.
- Fill in the initial information in the template.
- Clone the sample repository, if you're not testing against your own project.
- Run `simple_deploy` in either configuration mode, or the automated mode.
- Summarize your results, in as much or as little detail as you care to provide. We are mosted interested in:
    - Did the project work as you expected it to?
    - Was the documentation clear?
    - Was the configuration successful?
    - Was the deployment successful?
    - What questions do you have?
    - What suggestions do you have?

## Detailed Instructions

Here are the detailed instructions for making a test run against the example project. The example project uses a bare `requirements.txt` file.

### Run the project locally

Clone the example project, and run it locally:

=== "macOS/Linux"

    ```
    $ git clone https://github.com/ehmatthes/dsd_sample_blog_reqtxt.git
    $ cd dsd_sample_blog_reqtxt
    $ python3 -m venv b_env
    $ source b_env/bin/activate
    (b_env)$ pip install --upgrade pip
    (b_env)$ pip install -r requirements.txt
    (b_env)$ python manage.py migrate
    (b_env)$ python manage.py runserver
    ```

=== "Windows"

    ```
    > git clone https://github.com/ehmatthes/dsd_sample_blog_reqtxt.git
    > cd dsd_sample_blog_reqtxt
    > python -m venv b_env
    > b_env\Scripts\activate
    (b_env)> pip install --upgrade pip
    (b_env)> pip install -r requirements.txt
    (b_env)> python manage.py migrate
    (b_env)> python manage.py runserver
    ```

At this point you may want to visit the site and make an account, and maybe make a post. You may also want to visit the admin page, and verify that everything's working locally.

### Run functionality tests against the local project

The functionality tests use `requests`; these are not typical tests for a Django project. They're written this way to facilitate testing deployed versions of the project, as a user would interact with them. You can run these tests against the local project if you want. Open a new terminal tab, activate the virtual environment, and run the following command:

```sh
(b_env)$ python test_deployed_app_functionality.py --url http://localhost:8000
```

The tests are meant to be run against a freshly-deployed version of the project, with no user data. If you get errors, you may need to rerun the tests using the `--flush-db` flag, which only works when testing the local version of the project:

```sh
(b_env)$ python test_deployed_app_functionality.py --flush-db --url http://localhost:8000
```

### Run `simple_deploy` against the sample project

Now you have a simple but nontrivial Django project that works locally, with no deployment-specific configuration. This is exactly the situation that `simple_deploy` is meant to handle.

Visit the [Quick Start](../quick_starts/index.md) document for the platform you're targeting, and follow the directions you see there.

### Evaluating the deployment

If the deployment was not successful, please provide as much information as you can that will help us troubleshoot the project.

If the deployment was successful, you can run the automated tests against the deployed project. Remember that `--flush-db` won't work on the deployed project, so consider running these tests before entering any data on the deployed site. To run the tests:

```sh
(b_env)$ python test_deployed_app_functionality.py --url https://deployed-project-url
```

After running the tests, poke around the site on your own as well. Make sure you can make an account, make a blog and a post, and visit the admin site. (You'll need to make a superuser account on your own; `django-simple-deploy` does not do this for you.)

### Destroying the test project

Make sure you destroy your test deployment. This is entirely your responsibility, and if you fail to do so you will accrue any charges associated with a project deployed to the platform you are working with. No one associated with this project should ask you to keep a deployment alive for troubleshooting purposes.

### Final thoughts

If you have any final thoughts about how `django-simple-deploy` works, please share them in the issue you created to track your test run. Thank you for helping out!

## What next?

Feel free to do as many test runs as you want. For example you might want to deploy to a different platform, or try a different dependency management system, or deploy a different project.

This is also a great time to try running the [integration tests](https://github.com/ehmatthes/django-simple-deploy/blob/main/old_docs/integration_tests.md) for the platform you just targeted. Integration tests automate everything you just did. (Documentation for integration tests has not been migrated here yet.)

If you want to contribute in other ways, see the main [Contributing](index.md) page for a variety of ways to help out.
