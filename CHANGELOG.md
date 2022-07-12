Changelog: django-simple-deploy
===

For inspiration and motivation, see [Keep a CHANGELOG](https://keepachangelog.com/en/0.3.0/).

0.4 - Supporting Heroku & Platform.sh

### 0.4.1

- Simplified MANIFEST.in
    - No user-facing changes, but built release to verify that changes don't break the release process.

### 0.4.0

- Removed support for Azure.
  - See detailed rationale in [Stop supporting Azure](https://github.com/ehmatthes/django-simple-deploy/issues/83).
  - Brief rationale: Focus django-simple-deploy on platforms like Heroku and Platform.sh where everything is contained in a single project, rather than a collection of services.
  - May resume support at some point in the future, but the project needs to evolve further before resuming this support.
  - Azure was used as a proof-of-concept to try supporting multiple platforms. Since then, I have had time to explore other platforms that are more suitable targets for django-simple-deploy.

0.3 - Supporting Heroku, Azure, & Platform.sh

### 0.3.0

- Preliminary support for platform.sh
    - If you have a platform.sh account, have installed the CLI, are using Git,
    and have a `requirements.txt` file, running
    `$ python manage.py simple_deploy --platform platform_sh`
    should configure your project for deployment on Platform.sh.
    - Then you'll need to commit changes, run `platform create`, and `platform push`.
    - Project should open with `platform url`.

0.2 - Supporting Heroku & Azure
---

### 0.2.5

- Fix image loading issue in main README on PyPI.

### 0.2.4

- Set up local unit testing (testing with no network calls).
- Moved all testing documentation to docs/.
- Simplified approach to the `ALLOWED_HOSTS` setting for Heroku deployments.
    - If the Heroku host is not found, append the Heroku host to `ALLOWED_HOSTS` in the Heroku-specific settings section, regardless of what else is in `ALLOWED_HOSTS`. This is motivated by reports from users who have followed tutorials that advise them to modify `ALLOWED_HOSTS` in a variety of ways. Appending our host in a Heroku-specific settings section should not cause any foreseeable problems.
    - Also improved unit testing. Tests can be run against multiple versions of the sample project, by modifying the project after it's created. This does not add significantly to test runtimes.

### 0.2.3

- Added documentation of [full set of CLI arguments](docs/cli_args.md).
- Progress towards supporting projects with a nested directory structure.
    - This is for projects started with `django-admin startproject project_name`, without a dot.
    - Includes nested version of sample blog project.
- Fixes bug on Windows, where system commands were not running.
- Steadily improving internal structure.

### 0.2.2

- Writes verbose log file; adds log directory to .gitignore.

### 0.2.1

- Simplified the integration testing scripts significantly.
- Added brief [roadmap](docs/roadmap.md).
- Added brief [contributing guide](docs/contributing.md).
- Added a [Code of Conduct](docs/code_of_conduct.md).
- SECRET_KEY on Heroku uses a config variable.
- DEBUG on Heroku uses a config variable.

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