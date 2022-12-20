Changelog: django-simple-deploy
===

For inspiration and motivation, see [Keep a CHANGELOG](https://keepachangelog.com/en/0.3.0/).

0.5 - Supporting Fly.io, Platform.sh, and Heroku
---

### 0.5.14

#### External changes

- Clarified documentation about configuration-only mode. We do sometimes create remote resources on the user's behalf, but only when we can't easily ask users to do so before running `simple_deploy`.
- All three platforms now support all three dependency management systems (bare `requirements.txt` file, Poetry, and Pipenv).
- Updated documentation about unit tests.
- Official documentation includes a roadmap, with a focus on reaching a 1.0 release.

#### Internal changes

- Started platform-agnostic tests for the process of inspecting local projects.
- The check for whether Poetry is being used is more specific.
- Every unit test now runs once for each dependency management system.
- The dependency management system is identified in `simple_deploy.py`, but platform-specific scripts make all decisions about what to do with that information.
    - Better internal support for platforms to work with requirements. There's a simple `add_package()` method in `simple_deploy.py`, as well as `add_packages()`. These then call the appropriate method for the current dependency management system in use.
    - Docker-based platforms make appropriate use of specific package managers, ie creating an optional `deploy` group in `pyproject.toml` when Poetry is being used.

### 0.5.13

#### External changes

- The output of `manage.py simple_deploy --help` is significantly improved.
- CLI-related error messages have been improved.
- The CLI is thoroughly documented on RtD.


#### Internal changes

- Moved all platform-specific files to their own directory. The only reference to a specific platform in *simple_deploy.py* is now the validation of the platform name.
    - Simplified *setup.cfg* to only refer to the `simple_deploy` package.
    - Simplified use of the Django template engine to write and modify files for configuration; see `write_file_from_template()` in *utils.py*.
    - Platform-specific imports are now done dynamically in *simple_deploy.py*, so only the files for the targeted platform are actually imported.
- Implementation of the CLI has been improved:
    - All CLI args are now defined in a separate module, `cli.py`.
    - Help output is covered in a unit test.
- Other developer-focused documentation improvements:    
    - Documented maintenance of docs.
    - Started ADR documentation.
    - Added Black to requirements, and used it to format the new `cli.py` file.

### 0.5.12

#### External changes:
- Removes local dependence on `platformshconfig`. Uses `os.environ.get()` locally to check whether deployment-specific settings should be used.

### 0.5.11

#### External changes:
- Fixed validation of `--platform` argument when used with `--automate-all`.

#### Internal changes:
- Removed `execute_subp_run_parts()`, and using `shlex.split(cmd)` instead of `cmd.split()`.

### 0.5.10

- Streams output of `platform create` when deploying to Platform.sh using `--automate-all`. This makes it more clear that the deployment has not hung on the `create` step.

### 0.5.9

- When configuring for Fly.io deployments, uses whitenoise to serve static files. Runs collectstatic during the build process.

### 0.5.8

- Updated unit test suite.
    - Unit test runs add `simple_deploy` to `INSTALLED_APPS` after last commit, like most end users would.
    - Unit tests are reorganized to separate tests for each platform, and to have a dedicated set of platform-agnostic tests.
    - Most shell scripts have been moved to a `utils/` directory.
    - A much simpler approach to testing invalid CLI calls is used.
    - Includes a basic set of unit tests for Fly.io configuration .
    - Each `unit_tests/platforms/` dir contains a `reference_files` directory. When unit tests run, modified sample project files are compared to these reference files. This makes it much easier to reason about unit tests, and provides a nice set of files to see exactly what changes `simple_deploy` makes to the sample project's files.
    - The sample project is only built once for every test session, rather than once per test module. The test project is reset for each new test module. This results in a speedup from ~52s to ~16s for the entire suite at this point. More importantly, testing more platforms and dependency management approaches will only incrementally increase test duration, rather than multiplying test duration.
    - Official documentation covers how to run unit tests. This update also includes some minor but important updates to the unit tests. These updates center around a better use of `autouse=True` where appropriate, and better use and explanation of scope.
    - In unit tests, we make sure the main branch is named `main`. Some tests expect to see references to the `main` branch in CLI output, and this would have failed on any contributor or CI system with a different default branch name.
- Configuration works when the target project's `settings.BASE_DIR` is a string. This affects any project whose setting file was generated in Django 3.0 or earlier, and hasn't been updated to use `Path` objects.
- When configuring for Heroku deployments, Whitenoise is added to middleware. This fixes a bug where the admin site on Heroku deployments does not have access to static resources such as css and js.

### 0.5.7

- Started the Contributing section on the official documentation:
  - Main contributing page
  - Documenting a Test Run
  - Testing on Your Own Account
  - Setting up a Development Environment
- Added issue template for documenting test runs. 
- Deployments on Platform.sh no longer include a `.platform/routes.yaml` file. 

### 0.5.6

- Documentation for managing PRs and releases moved to Read the Docs.
- Documentation includes installing `platformshconfig` when deploying to Platform.sh.
- Removes auto-update block from `.platform.app.yaml`.
- Integration tests check that running simple_deploy does not affect local functionality using `runserver`.
    - Update configuration for Fly.io and Platform.sh to not interfere with local functionality using `runserver`.
- Updated sample blog project to Django 4.1.2.
    - Modified `test_deployed_app_functionality.py` to not require a trailing forward slash.
    - Added notes about the differences between nested and non-nested projects.
- Deployments to Fly.io use the deployed project name in `ALLOWED_HOSTS` and `CSRF_TRUSTED_ORIGINS` settings.

### 0.5.5

- Streams output of `platform push`.

### 0.5.4

- Streams output of long-running commands `fly postgres create` and `fly deploy`. This makes it much easier to know that the deployment is continuing, rather than hanging.

### 0.5.3

- Generates a `.dockerignore` file when deploying to Fly.io.

### 0.5.2

- Uses [updated Dockerfile](https://github.com/superfly/flyctl/pull/1366) from Fly.io.
- The `-y` flag skips confirmation for teardown when running integration tests.

### 0.5.1

- Official documentation moved to [Read the Docs](https://django-simple-deploy.readthedocs.io/en/latest/).
    - Quick-start guides for all three supported platforms.
- Better check of `git status` when running `simple_deploy`. If the only uncommitted change is adding `simple_deploy` to `INSTALLED_APPS`, no error is raised.

### 0.5.0

- Preliminary support for Fly.io
    - Configuration-only and `--automate-all` approaches work on my macOS.
    - Probably only works when you don't have any other Fly.io projects deployed.
    - No documentation for Fly.io yet.
    - No unit tests yet.
    - Integration tests work.

0.4 - Supporting Heroku & Platform.sh
---

### 0.4.3

- Refining support of Platform.sh:
    - Initial unit tests for Platform.sh.
    - Initial integration tests written for Platform.sh.
    - `DEBUG = False` by default on Platform.sh.
    - Check that `platform create` has been run, or that a deployed project name has been provided.
    - More informative error messages if any prerequisite conditions are not met, such as running `platform create`.
    - `--automate-all` now works on Platform.sh.
    - Improved success messages after configuration-only run.
- Significant restructuring of simple_deploy's architecture, to more cleanly separate platform-agnostic work from platform-specific work. For example, see [Issue 89](https://github.com/ehmatthes/django-simple-deploy/issues/89).
- More integrity checks before making any configuration changes:
    - Check `git status` before beginning configuration work. Warn users and exit if status is not `working tree clean`. The `--ignore-unclean-git` flag will override this warning.
    - Check that Platform.sh CLI or Heroku CLI are installed before configuring for those platforms.
- Developer-focused improvements:
    - Added a `-y` flag to integration test script, to skip bash script confirmations.
    - Separated `--local-test` flag into `--unit-testing` and `--integration-testing` flags.

### 0.4.2

- Requires `--platform` flag.
    - There's no reason to have a default platform; deployment is a significant enough step that users should have a specific deployment target in mind. If the `--platform` flag is omitted, exit with a message displaying a list of platforms that are supported.

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
---

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
- Moved all testing documentation to old_docs/.
- Simplified approach to the `ALLOWED_HOSTS` setting for Heroku deployments.
    - If the Heroku host is not found, append the Heroku host to `ALLOWED_HOSTS` in the Heroku-specific settings section, regardless of what else is in `ALLOWED_HOSTS`. This is motivated by reports from users who have followed tutorials that advise them to modify `ALLOWED_HOSTS` in a variety of ways. Appending our host in a Heroku-specific settings section should not cause any foreseeable problems.
    - Also improved unit testing. Tests can be run against multiple versions of the sample project, by modifying the project after it's created. This does not add significantly to test runtimes.

### 0.2.3

- Added documentation of [full set of CLI arguments](old_docs/cli_args.md).
- Progress towards supporting projects with a nested directory structure.
    - This is for projects started with `django-admin startproject project_name`, without a dot.
    - Includes nested version of sample blog project.
- Fixes bug on Windows, where system commands were not running.
- Steadily improving internal structure.

### 0.2.2

- Writes verbose log file; adds log directory to .gitignore.

### 0.2.1

- Simplified the integration testing scripts significantly.
- Added brief [roadmap](old_docs/roadmap.md).
- Added brief [contributing guide](old_docs/contributing.md).
- Added a [Code of Conduct](old_docs/code_of_conduct.md).
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