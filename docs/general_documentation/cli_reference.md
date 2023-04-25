---
title: Command Line Reference
hide:
    - footer
---

# Command Line Reference

`django-simple-deploy` is a command line tool, and there are a number of options you can use to customize its behavior.

## Help output

For a quick summary of the most important CLI options, run `manage.py simple_deploy --help`. Here's the output:

```sh
$ python manage.py simple_deploy --help
usage: manage.py simple_deploy --platform PLATFORM_NAME
        [--automate-all]
        [--no-logging]
        [--ignore-unclean-git]

        [--region REGION]
        [--deployed-project-name DEPLOYED_PROJECT_NAME]

Configures your project for deployment to the specified platform.

Get help:
  --help, -h            Show this help message and exit.

Required arguments:
  --platform PLATFORM, -p PLATFORM
                        Specifies the platform where the project will be deployed. Options: fly_io | platform_sh |
                        heroku

Customize simple_deploy's behavior:
  --automate-all        Automates all aspects of deployment. Creates resources, makes commits, and runs `push` or
                        `deploy` commands.
  --no-logging          Do not create a log of the configuration and deployment process.
  --ignore-unclean-git  Run simple_deploy even with an unclean `git status` message.

Customize deployment configuration:
  --deployed-project-name DEPLOYED_PROJECT_NAME
                        Provide a name that the platform will use for this project.
  --region REGION       Specify the region that this project will be deployed to.

For more help, see the full documentation at: https://django-simple-deploy.readthedocs.io
```

## Required arguments

### `--platform`, `-p`

When you're deploying a project, you need to target a specific platform. This is designated by the `--platform` argument. Currently supported platforms are `fly_io`, `platform_sh`, and `heroku`.

Example usage:

```sh
$ python manage.py simple_deploy --platform fly_io
```

## Customizing behavior

There are several options to customize `simple_deploy`'s behavior. You can automate the entire deployment process, skip logging, and ignore the output of `git status` when deploying.

### `--automate-all`

The recommended (default) way to use `simple_deploy` is in configuration mode. In this mode, `simple_deploy` makes all configuration changes necessary to successfully deploy your project on the given platform. However, it avoids creating any remote resources it doesn't have to, and it does not any commits on your behalf. This is good, because it lets you know exactly what you need to create, and you get to review all changes before committing them to your project.

The `--automate-all` flag tells `simple_deploy` to do everything for you: it creates any resources necessary for deployment on the target platform. It makes all the necessary configuration changes, and makes a new commit for these changes. Finally, it calls your platform's `push` or `deploy` command; you get to sit back and watch your deployed project appear in a new browser tab.

Example usage:

```sh
$ python manage.py simple_deploy --platform PLATFORM_NAME --automate-all
```

If you choose this option, you'll see a summary of what will be done on your behalf, and you'll need to confirm this is the behavior you want.

### `--no-logging`

By default, `simple_depoy` creates a new directory at your project's root level called `simple_deploy_logs`. This directory is added to `.gitignore`, so it won't be pushed as part of your deployed project, and it won't be pushed to your project's repo.

Inside `simple_deploy_logs`, a new log file is written each time you call `simple_deploy`. This is a record of most of the output you see in the terminal. It's useful for looking back on what changes were made during the configuration process, and for troubleshooting anything that went wrong. We are also working on a friendly summary of the deployment process, with links to the most relevant parts of your platform's documentation, and a summary of how to build on your initial deployment.

If you want to skip logging, you can pass the `--no-logging` flag.

Example usage:

```sh
$ python manage.py simple_deploy --platform PLATFORM_NAME --no-logging
```

### `--ignore-unclean-git`

When you run `simple_deploy`, it calls `git status` and examines the result. It's looking for a clean state, although it won't complain if the only change detected is the addition of `simple_deploy` in `INSTALLED_APPS`.

There's a very good reason for this: `simple_deploy` is going to modify your project, by making some new files and modifying existing files. It should do this right, but it may not. If you have a clean git status, you can undo the changes that `simple_deploy` makes by rolling back to your most recent commit. If `simple_deploy` runs without a clean git status, it would be much harder to undo the changes that it makes.

If you have a specific reason to run `simple_deploy` without a clean state, you can pass the `--ignore-unclean-git` flag.

Example usage:

```sh
$ python manage.py simple_deploy --platform PLATFORM_NAME --ignore-unclean-git
```

## Customizing configuration

The goal of `simple_deploy` is to keep configuration for deployment as simple as possible. We make most configuration decisions for you, so you don't have to make those decisions for your initial push. However, some deployments may need a little extra configuration information.

### `--deployed-project-name DEPLOYED_PROJECT_NAME`

For some deployments, you may need to specify the name of the project on the target platform. By default, `simple_deploy` tries to use the same name you used when you ran `django-admin startproject PROJECT_NAME`. However, you may have already created a resource on your platform with a different name, or the platform may have created a resource with a different name for you.

If you need to specify the deployed project name, use the `--deployed-project-name`:

```sh
$ python manage.py simple_deploy --platform PLATFORM_NAME --deployed-project-name DEPLOYED_PROJECT_NAME
```

??? note
    This flag is used in some testing scripts to avoid making network calls to discover the name a platform has chosen for a resource.

### `--region`

When you deploy a project to a hosting service, they start up a virtual server on a physical machine in a datacenter somewhere in the world. Some platforms default to a datacenter near you, while others may default to a server far from your location. The `--region` flag lets you specify a region where your project should be deployed.

Example usage:

```sh
$ python manage.py simple_deploy --platform PLATFORM_NAME --region REGION
```

This flag does not take effect for all platforms, and the argument you provide must be one that your platform's CLI recognizes.

## Developer-focused options

There are two developer-focused options that don't show up in the `manage.py simple_deploy --help` output. These are focused on testing.

### `--unit-testing`

This is a flag that tells `simple-deploy` that we're running unit tests. This overrides any action that would involve a network call. We rarely use this flag ourselves. Instead, it's used when `simple_deploy` is called from a unit testing script, such as `unit_tests/utils/call_simple_deploy.sh`.

### `--integration-testing`

This is a flag that's used when running integration tests. It is primarily used to override confirmations for streamlined integration test runs, which carry out actual deployments. This flag is rarely used directly on the command line; it's mainly used in scripts such as `integration_tests/test_flyio_deployment.sh`.

## Default Django options

Custom Django management commands inherit a number of default options, common to all management commands. The documentation shown here is the same as what you'll see if you run the help command for any default Django management command, such as `manage.py help check`, which displays the help information for the `manage.py check` command.

These options aren't displayed in the output for `manage.py simple_deploy --help` because they're not often used when running `simple_deploy`. They are still available, however, if you need to include any of them.

### `--version`

Reports which version of Django is currently installed.

### `--verbosity, -v {0, 1, 2, 3}`

This controls how much information you want to see in the command output.

- 0: minimal output
- 1: normal output
- 2: verbose output
- 3: very verbose output

### `--settings SETTINGS`

The Python path to a settings module, such as `my_project.settings.main`. If this isn't provided, the `DJANGO_SETTINGS_MODULE` environment variable will be used. In a standard Django project, this is the `settings.py` file that's generated when you run `django-admin startproject PROJECT_NAME`.

### `--pythonpath PYTHONPATH`

A directory to add to the Python path, such as `/home/djangoprojects/myproject`.

### `--traceback`

This tells Django to raise `CommandError` exceptions, rather than handling them automatically.

### `--no-color`

This tells Django not to colorize command output.

### `--force-color`

This tells Django to force colorization of the command output.
