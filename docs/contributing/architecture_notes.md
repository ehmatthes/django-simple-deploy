---
title: Architecture Notes
hide:
    - footer
---

# Architecture Notes

This page describes some aspects of the structure of the project.

## Access to platform-specific messages

The `simple_deploy.py` script needs access to some platform-specific messages. The platform deployer object should provide access to those messages.

## Checking for unit testing

There are many network calls that don't need to be made when unit testing. These checks are typically placed at the lowest level possible, to keep the workflows in higher level methods simple and readable.

## Checking for `--automate-all`

Likewise, checks for automate-all are usually in lower-level functions, to keep higher-level functions simpler.

---

## Contract between host and plugin

This is a parking lot for notes about implementing the plugin model.

### What does the host provide the plugin?

- Host inspects project, and makes relevant information about the project available, such as path to root directory, os, package manager in use, etc. (List all that's provided.)
- Utility functions for common operations, ie writing to log and writing to console, running fast and slow commands.

### What must the plugin provide to the host?

- A `PlatformDeployer` class that can be instantiated.
- The `platform_deployer` object must have a `messages` attribute, for platform-specific messages.
    - The host must provide a `confirm_automate_all` message.

    
### What *should* the plugin do?

These are not hard requirements, but should probably be done by every deploy script. This may separate out into CLI-based workflows, API-based workflows, and GH-based workflows.

- Verify that the platform's CLI is installed.
- Verify that the user has authenticated through the CLI.
- Verify that any pre-requisite resources have already been created.

### What structure should the plugin have?

Something roughly like this:

```sh
$ tree -L 2
├── deploy.py
├── deploy_messages.py
├── templates
│   ├── pipenv.platform.app.yaml
│   ├── platform.app.yaml
│   ├── poetry.platform.app.yaml
│   ├── services.yaml
│   └── settings.py
├── tests
│   └── unit_tests
└── utils.py
```