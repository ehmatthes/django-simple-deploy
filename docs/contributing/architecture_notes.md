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