Changelog: django-simple-deploy
===

For inspiration and motivation, see [Keep a CHANGELOG](https://keepachangelog.com/en/0.3.0/).

0.2 - Supporting Heroku & Azure
---

### 0.2.1

- Unreleased.
- Simplified the integration testing scripts significantly.
- Added brief [roadmap](docs/roadmap.md).
- Added brief [contributing guide](docs/contributing.md).

### 0.2.0

- Preliminary support for Azure deployments.

0.1 - Supporting Heroku
---

### 0.1.11

- Supports Python 3.8, because Azure is still on 3.8.

### 0.1.10

- Bugfix to address import error in deploy_heroku.py.

### 0.1.9

- Bugfix: Minor bugs were causing issues with final message after deployment process had been completed.

### 0.1.8

- External changes:
    - `simple_deploy` accepts a `--platform` argument. The default, and only meaningful value at the moment is `heroku`. However, this change makes it possible to begin targeting other platforms.

- Internal changes:
    - Testing script is broken into platform-agnostic, and Heroku-specific files.
    - Test script accepts a platform argument: `$ autoconfigure_deploy_test.sh -o automate_all -p heroku`. Heroku is default value, and is the only meaningful value at the moment.

### 0.1.7

- Internal changes:
    - All multiline output messages defined in a separate module.
    - Reviewed all existing comments. (11/5/21)
    - Refactored code that adds Heroku-specific settings.

### 0.1.6

- Includes `--automate-all` flag.

### 0.1.5

- Supports projects that use Poetry.

### 0.1.4

- Supports projects that use Pipenv.

### 0.1.3

- Makes Heroku install from PyPI instead of the GitHub repo.

### 0.1.2

- Added change log.
- Expanded main README to include detailed steps, and more.

### 0.1.1

- Fixed markdown formatting issue on PyPI.

### 0.1.0

- Initial functionality; works for my project.