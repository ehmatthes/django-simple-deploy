---
title: "Setting Up a Development Environment"
hide:
    - footer
---

# Setting Up a Development Environment

- fork
- clone
- copy blog to a separate repo
- in that environment, set up and run local tests
- then pip install -e
- add simple_deploy to installed_apps
- make a commit
- hack
- run your deployment work
- you can use `manage.py simple_deploy --unit-testing` to see configuration changes, without making a deployment
- reset --hard commit_hash to undo config changes
- make sure git status, and delete anything that didn't get reset, ie simple_deploy_logs/