---
title: Command Line Reference
hide:
    - footer
---

# Command Line Reference

`django-simple-deploy` is a command line tool, and there are a number of options you can use to customize its behavior.

## Help output

For a quick summary of the most important CLI options, run `manage.py simple_deploy --help`. Here's the output:

```
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

```
$ python manage.py simple_deploy --platform fly_io
```

## Customizing behavior

There are several options to customize `simple_deploy`'s behavior. You can automate the entire deployment process, skip logging, and ignore the output of `git status` when deploying.

### `--automate-all`

The recommended way to use `simple_deploy` is in configuration mode. In this mode, `simple_deploy` makes all configuration changes necessary to successfully deploy your project on the given platform. However, it does not commit these changes, it does not create any resources on your behalf, and it doesn not commit any changes. This is good, because it lets you know exactly what you need to create, and you get to review all changes before committing them to your project.

The `--automate-all` flag tells `simple_deploy` to do everything for you: it creates any resources necessary for deployment on the target platform. It makes all the necessary configuration changes, and makes a new commit for these changes. Finally, it calls your platform's `push` or `deploy` command; you get to sit back and watch your deployed project appear in a new browser tab.

Example usage:

```
$ python manage.py simple_deploy --platform PLATFORM_NAME --automate-all
```

If you choose this option, you'll see a summary of what will be done on your behalf, and you'll need to confirm this is the behavior you want.

### `--no-logging`

By default, `simple_depoy` creates a new directory at your project's root level called `simple_deploy_logs`. This directory is added to `.gitignore`, so it won't be pushed as part of your deployed project, and it won't be pushed to your project's repo.

Inside `simple_deploy_logs`, a new log file is written each time you call `simple_deploy`. This is a record of most of the output you see in the terminal. It's useful for looking back on what changes were made during the configuration process, and for troubleshooting anything that went wrong. We are also working on a friendly summary of the deployment process, with links to the most relevant parts of your platform's documentation, and a summary of how to build on your initial deployment.

If you want to skip logging, you can pass the `--no-logging` flag.

Example usage:

```
$ python manage.py simple_deploy --platform PLATFORM_NAME --no-logging
```

### `--ignore-unclean-git`

When you run `simple_deploy`, it calls `git status` and examines the result. It's looking for a clean state, although it won't complain if the only change detected is the addition of `simple_deploy` in `INSTALLED_APPS`.

There's a very good reason for this: `simple_deploy` is going to modify your project, by making some new files and modifying existing files. It should do this right, but it may not. If you have a clean git status, you can undo the changes that `simple_deploy` makes by rolling back to your most recent commit. If `simple_deploy` runs without a clean git status, it would be much harder to undo the changes that it makes.

If you have a specific reason to run `simple_deploy` without a clean state, you can pass the `--ignore-unclean-git` flag.

Example usage:

```
$ python manage.py simple_deploy --platform PLATFORM_NAME --ignore-unclean-git
```

## Customizing configuration



## Developer-focused options