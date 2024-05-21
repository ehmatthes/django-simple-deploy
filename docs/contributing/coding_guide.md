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

## Coding Style

Use `black` when possible. At this point, some files may not follow Black conventions. By the 1.0 release, Black can act globally across the codebase.

## Python usage

### Use `path.read_text()` when possible.

We are passing paths around most of the time. Use `path.read_text()`, rather than `with open(filename)`.

