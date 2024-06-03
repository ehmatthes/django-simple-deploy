---
title: "Coding Guide"
hide:
    - footer
---

# Coding Guide

There are some coding guidelines that are helpful to note, with the following goals:

- Maintain consistent conventions and usage across the codebase.
- Use simple approaches whenever possible.
- Make it as easy as possible for new contributors to start contributing to the project.

# Project structure

As much as possible, write small utility functions that can easily be unit tested, without the need for building a full project.

## Coding Style

Use `black` when possible. At this point, some files may not follow Black conventions. By the 1.0 release, Black can act globally across the codebase.

## Python usage

### Use `path.read_text()` when possible.

We are passing paths around most of the time. Use `path.read_text()`, rather than `with open(filename)`.


## Working with plugins

### Return values

When you call out to a function implemented by a plugin that returns a value, that value is packed into a list. Often we're just dealing with one plugin, so you'll see code that looks like this:

```python
automate_all_msg = pm.hook.simple_deploy_get_automate_all_msg()[0]
```