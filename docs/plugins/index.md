---
title: Plugins
hide:
    - footer
---

# Plugins

Plugins are critical to the functioning of this project. Plugins don't just extend the functionality of django-simple-deploy; they implement *all* platform-specific functionality. The core project inspects the user's project and system, and then hands off to the plugin for all platform-specific configuration work.

## Developing a new plugin

I'm aiming to make a repo that will serve as a template for starting a new plugin. Until then, the best approach is to copy what you see in the [dsd-flyio](https://github.com/django-simple-deploy/dsd-flyio) plugin. If you're interested in developing a new plugin and want some help, please feel free to open an issue.

- Start by downloading the `dsd-plugin-template` repo, and follow instructions in the README. This will give you a working plugin, which you can customize for your platform.

## Testing plugins

The test suite will identify a plugin that's installed in editable mode, and run that platform's unit and integration tests.
