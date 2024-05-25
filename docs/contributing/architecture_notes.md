---
title: Architecture Notes
hide:
    - footer
---

# Architecture Notes

This page describes some aspects of the structure of the project.

## Access to platform-specific messages

The `simple_deploy.py` script needs access to some platform-specific messages. The platform deployer object should provide access to those messages.

---

## Contract between host and plugin

This is a parking lot for notes about implementing the plugin model.

### What must the plugin provide to the host?

- A `PlatformDeployer` class that can be instantiated.
- The `platform_deployer` object must have a `messages` attribute, for platform-specific messages.
    - The host must provide a `confirm_automate_all` message.

    
### What *should* the plugin do?

These are not hard requirements, but should probably be done by every deploy script. This may separate out into CLI-based workflows, API-based workflows, and GH-based workflows.

- Verify that the platform's CLI is installed.
- Verify that the user has authenticated through the CLI.
- Verify that any pre-requisite resources have already been created.