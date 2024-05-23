---
title: Architecture Notes
hide:
    - footer
---

# Architecture Notes

This page describes some aspects of the structure of the project.

## Access to platform-specific messages

The `simple_deploy.py` script needs access to some platform-specific messages. The platform deployer object should provide access to those messages.