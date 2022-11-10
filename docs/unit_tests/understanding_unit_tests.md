---
title: "Understanding the Unit Tests"
hide:
    - footer
---

# Understanding the Unit Tests

The unit test suite for `django-simple-deploy` is likely to grow increasingly complex over time. If you haven't done extensive testing, it can be a little overwhelming to dig into the test suite as a whole. The goal of this page is to explain the structure of the unit test suite, so that it continue to run efficiently and effectively as the project evolves.

The complexity comes from trying to do all of the following:

- Run tests that focus on the CLI.
- Run tests that target multiple platforms.
- Run tests that focus on different dependency management systems. *(not yet implemented)*
- Run tests against nested and unnested versions of the sample project. *(not yet implemented)*
- Run tests against multiple versions of Django. *(not yet implemented)*
- Run tests against multiple versions of Python. *(not yet implemented)*

For every test run listed here, `simple_deploy` needs to be called against a fresh version of the sample project. That's a lot of testing!

## Organization of the test suite

Here's the file structure of the unit test suite:

```
unit_tests $ tree -L 4
.
├── __init__.py
├── conftest.py
├── platform_agnostic_tests
│   └── test_invalid_cli_commands.py
├── platforms
│   ├── fly_io
│   │   ├── reference_files
│   │   │   ├── Dockerfile
│   │   │   ├── fly.toml
│   │   │   ├── requirements.txt
│   │   │   └── settings.py
│   │   └── test_flyio_config.py
│   ├── heroku
│   │   ├── modify_allowed_hosts.sh
│   │   ├── reference_files
│   │   │   ├── Procfile
│   │   │   ├── placeholder.txt
│   │   │   ├── requirements.txt
│   │   │   └── settings.py
│   │   └── test_heroku_config.py
│   └── platform_sh
│       ├── reference_files
│       │   ├── requirements.txt
│       │   ├── services.yaml
│       │   └── settings.py
│       └── test_platformsh_config.py
└── utils
    ├── call_git_log.sh
    ├── call_git_status.sh
    ├── call_simple_deploy.sh
    ├── call_simple_deploy_invalid.sh
    ├── commit_test_project.sh
    ├── reset_test_project.sh
    ├── setup_project.sh
    └── ut_helper_functions.py

9 directories, 26 files
```

Let's go through this from top to bottom:

- We need an `__init__.py` file at the root of `unit_tests/` so nested test files can import from `utils/`.
- `conftest.py` contains two fixtures[^1]:
    - `tmp_project()` creates a temporary directory for the copy of the sample project we're going to test against. It calls `utils/setup_project.sh` which copies the sample project, builds a virtual environment, makes an initial commit, and adds `simple_deploy` to the test project's `INSTALLED_APPS`. It has a session-level scope[^2], and returns the absolute path to the temporary directory where the test project will live.
    - `reset_test_project()` resets the sample project so we can run `simple_deploy` again, without having to rebuild the entire test project environment. It does this by calling `utils/reset_test_project.sh`. This fixture has a module-level scope.
- `platform_agnostic_tests` contains a set of tests that don't relate to any specific platform.
    - `test_invalid_cli_commands.py` tests invalid ways users might call `simple_deploy`, without a valid `--platform` argument.
- The `platforms` directory contains all platform-specific test files.
    - In the `fly_io` directory, `reference_files` contains files like `settings.py`, as they should look after a successful run of `simple_deploy` targeting deployment to Fly.io.
    - `test_flyio_config.py`
        - This file has a module-scoped fixture called `run_simple_deploy()`, which loads the `reset_test_project()` fixture and then calls `utils/call_simple_deploy.sh`. This runs `simple_deploy` with the appropriate `--platform` argument, and the `--unit-testing` flag.
        - It tests modification to project files such as `settings.py`, `requirements.txt`, and `.gitignore`.
        - It tests platform-specific files such as `fly.toml`, `Dockerfile`, and `.dockerignore`.
        - It tests that a log file is created, and that the log file contains platform-specific output.
    - The other directories in `platforms/` contain similar files for the other supported platforms. The file `heroku/modify_allowed_hosts.sh` is leftover from the earlier clunky way of starting to test special situations; this file will likely be removed before long.
- The `utils/` directory contains scrips that are used by multiple test files. (Some people think `utils/` is a bad name, like `misc`, but it's used here to imply that these scripts have utility across multiple test modules.)
    - `call_git_log.sh` and `call_git_status.sh` are used to verify that the test sample project hasn't been changed after running invalid variations of the `simple_deploy` command.
    - `call_simple_deploy_invalid.sh` modifies invalid commands to include the `--unit-testing` flag. This approach allows test functions to contain the exact variations of the `simple_deploy` command that we expect end users to accidentally use.
    - `commit_test_project.sh` lets fixtures make commits against the test project.
    - `ut_helper_functions.py` contains one function, `check_reference_file()`, that's used in all platform-specific tests. As the tests grow and get refactored periodically, I expect this module to expand to more than this one function.


[^1]: For the purposes of this project, a *fixture* is a function that prepares for a test, or set of tests. For example, we use a fixture to copy the sample project from `django-simple-deploy/sample_project/blog_project/` to a temporary directory, and then build a full virtual environment for that project. Another fixture is used to call `simple_deploy` against the sample project; yet another fixture is used to reset the project for subsequent tests. To learn more, see [About fixtures](https://docs.pytest.org/en/latest/explanation/fixtures.html) and [How to use fixtures](https://docs.pytest.org/en/latest/how-to/fixtures.html).

[^2]:
    Every fixture has a *scope*, which controls how often a fixture is loaded when it's needed. 

    - `scope="session"`: The fixture is loaded once for the entire test run; the fixture that sets up the sample test project has session-level scope.
    - `scope="module"`: The fixture is loaded once for each module where it's used; the fixture that resets the sample test project has module-level scope.
    - The other possibilities for scope are `function`, `class`, and `package`. These scopes are not currently used in the `django-simple-deploy` test suite.
    - Read more at [Scope: sharing fixtures across classes, modules, packages or session](https://docs.pytest.org/en/latest/how-to/fixtures.html#scope-sharing-fixtures-across-classes-modules-packages-or-session)



## Testing a single platform

With all that said, let's look at what actually happens when we test a single platform. We'll see in what order the resources described above are used. As an example, we'll look at what happens when we issue the following call:

```
(dsd_env)unit_tests $ pytest platforms/fly_io/
```

### Collecting tests

This command tells pytest to find all the files starting with `test_` in the `platforms/fly_io/` directory, and collect any function starting with `test_` in those files. In this case, that's just `test_flyio_config.py`, which contains seven functions starting with `test_`. 




## Testing multiple platforms

## Running platform-agnostic tests

## Running the entire test suite

## Extending tests

## Writing tests for a new platform

## pytest references

- [About fixtures](https://docs.pytest.org/en/latest/explanation/fixtures.html)
- [How to use fixtures](https://docs.pytest.org/en/latest/how-to/fixtures.html)
- [Autouse fixtures](https://docs.pytest.org/en/latest/how-to/fixtures.html#autouse-fixtures-fixtures-you-don-t-have-to-request)
- [How to capture stdout/stderr output](https://docs.pytest.org/en/7.2.x/how-to/capture-stdout-stderr.html)
- [Parametrizing fixtures](https://docs.pytest.org/en/latest/how-to/fixtures.html#parametrizing-fixtures)
- Fixture [scope](https://docs.pytest.org/en/latest/how-to/fixtures.html#scope-sharing-fixtures-across-classes-modules-packages-or-session)