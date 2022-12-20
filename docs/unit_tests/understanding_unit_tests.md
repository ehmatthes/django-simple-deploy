---
title: "Understanding the Unit Tests"
hide:
    - footer
---

# Understanding the Unit Tests

The unit test suite for `django-simple-deploy` is likely to grow increasingly complex over time. If you haven't done extensive testing, it can be a little overwhelming to dig into the test suite as a whole. The goal of this page is to explain the structure of the unit test suite, so that it continues to run efficiently and effectively as the project evolves.

The complexity comes from trying to do all of the following:

- Run tests that focus on the CLI.
- Run tests that target multiple platforms.
- Run tests that focus on different dependency management systems.
- Run tests against nested and unnested versions of the sample project. *(not yet implemented)*
- Run tests against multiple versions of Django. *(not yet implemented)*
- Run tests against multiple versions of Python. *(not yet implemented)*

For every test run listed here, `simple_deploy` needs to be called against a fresh version of the sample project. That's a lot of testing!

!!! note
    Some of what you see here may be a little out of date, ie exact directory and file listings. However, the ideas here are kept fully up to date. If you see something in the unit tests that you don't understand, please feel free to open an issue and ask about it.

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
```

Let's go through this from top to bottom.

### `__init__.py`

We need an `__init__.py` file at the root of `unit_tests/` so nested test files can import from `utils/`.

### `conftest.py`

This file contains four fixtures[^1]:

- `tmp_project()` creates a temporary directory where we can set up a full virtual environment for the sample project we're going to test against. It calls `utils/setup_project.sh` which copies the sample project, builds a virtual environment, makes an initial commit, and adds `simple_deploy` to the test project's `INSTALLED_APPS`. It has a session-level scope[^2], and returns the absolute path to the temporary directory where the test project was created.
- `reset_test_project()` resets the sample project so we can run `simple_deploy` repeatedly, without having to rebuild the entire test project for each set of tests. It does this by calling `utils/reset_test_project.sh`. This fixture has a module-level scope.
- `run_simple_deploy()` has a module-level scope, with `autouse=True`. This means the fixture runs automatically for all test modules in the test suite. An `if` block in the fixture makes sure it exits without doing anything if a specific platform is not being targeted. This fixture runs `reset_test_project()` immediately before running `simple_deploy`.
- `pkg_manager()` has a function-level scope. Any function that includes this fixture will have access to the parameter that specifies which dependency management system is currently being tested. It will return `req_txt`, `poetry`, or `pipenv`. We use this to know what changes to expect in the modified project.

### `platform_agnostic_tests/`

This directory contains a set of tests that don't relate to any specific platform.

- `test_invalid_cli_commands.py` tests invalid ways users might call `simple_deploy`, without a valid `--platform` argument.

### `platforms/`

This directory contains all platform-specific test files. Let's take a closer look at `fly_io/`:

- `reference_files/` contains files like `settings.py`, as they should look after a successful run of `simple_deploy` targeting deployment to Fly.io.
- `test_flyio_config.py` does the following:
    - Tests modifications to project files such as `settings.py`, `requirements.txt`, and `.gitignore`.
    - Verifies the creation of platform-specific files such as `fly.toml`, `Dockerfile`, and `.dockerignore`.
    - Tests that a log file is created, and that the log file contains platform-specific output.

The other directories in `platforms/` contain similar files for the other supported platforms.

!!! note
    The file `heroku/modify_allowed_hosts.sh` is leftover from the earlier clunky way of starting to test special situations; this file will likely be removed before long.

### `utils/`

The `utils/` directory contains scrips that are used by multiple test files.

- `call_git_log.sh` and `call_git_status.sh` are used to verify that the test sample project hasn't been changed after running invalid variations of the `simple_deploy` command.
- `call_simple_deploy_invalid.sh` modifies invalid commands to include the `--unit-testing` flag. This approach allows test functions to contain the exact variations of the `simple_deploy` command that we expect end users to accidentally use.
- `commit_test_project.sh` lets fixtures make commits against the test project.
- `ut_helper_functions.py` contains one function, `check_reference_file()`, that's used in all platform-specific tests. As the tests grow and get refactored periodically, I expect this module to expand to more than this one function.

!!! note
    Some people think `utils/` is a bad name, like `misc`, but it's used here to imply that these scripts have utility across multiple test modules.


[^1]: For the purposes of this project, a *fixture* is a function that prepares for a test, or set of tests. For example, we use a fixture to copy the sample project from `django-simple-deploy/sample_project/blog_project/` to a temporary directory, and then build a full virtual environment for that project. Another fixture is used to call `simple_deploy` against the sample project; yet another fixture is used to reset the project for subsequent tests. To learn more, see [About fixtures](https://docs.pytest.org/en/latest/explanation/fixtures.html) and [How to use fixtures](https://docs.pytest.org/en/latest/how-to/fixtures.html).

[^2]:
    Every fixture has a *scope*, which controls how often a fixture is loaded when it's needed. 

    - `scope="session"`: The fixture is loaded once for the entire test run; the fixture that sets up the sample test project has session-level scope.
    - `scope="module"`: The fixture is loaded once for each module where it's used; the fixture that resets the sample test project has module-level scope.
    - The other possibilities for scope are `function`, `class`, and `package`. These scopes are not currently used in the `django-simple-deploy` test suite. The default scope is `function`.
    - Read more at [Scope: sharing fixtures across classes, modules, packages or session](https://docs.pytest.org/en/latest/how-to/fixtures.html#scope-sharing-fixtures-across-classes-modules-packages-or-session)



## Testing a single platform

With all that said, let's look at what actually happens when we test a single platform; we'll see in what order the resources described above are used. As an example, let's look at what happens when we issue the following call:

```
(dsd_env)unit_tests $ pytest platforms/fly_io/
```

### Collecting tests

This command tells pytest to find all the files starting with `test_` in the `platforms/fly_io/` directory, and collect any function starting with `test_` in those files. In this case, that's just `test_flyio_config.py`, which contains seven functions starting with `test_`.

Once pytest finds a test function, it begins to set up the test run.

### Fixtures, again

Here's where fixtures come into play. pytest first runs any fixture with a scope that's relevant to the tests that are about to be run:

- All fixtures with `scope="session"` will be run.
- Any fixture with a scope relevant to the test function that's about to be run, with `autouse=True`, will be run.
- Any fixture whose name appears in the test function's list of paremeters will be run. 

#### The `tmp_project()` fixture

We have one fixture in `conftest.py` with session-level scope, `tmp_project()`. Here's the most important parts of `tmp_project()`:

```python
@pytest.fixture(scope='session')
def tmp_project(tmp_path_factory):
    ...
    tmp_proj_dir = tmp_path_factory.mktemp('blog_project')
    ...
    cmd = f'sh utils/setup_project.sh -d {tmp_proj_dir} -s {sd_root_dir}'
    ...
    return tmp_proj_dir
```

This fixture calls a [built-in fixture](https://docs.pytest.org/en/latest/reference/reference.html#std-fixture-tmp_path_factory), `tmp_path_factory`, which allows us to request temporary directories for use during test runs. These directories are managed entirely by pytest, so we don't have to worry about cleaning them up later.

We make a temporary directory, and assign the full path for this directory to `tmp_proj_dir`. We then call `setup_project.sh`. Finally, we return `tmp_proj_dir`. Any test function with `tmp_project` in its paremeter list will have access to this value.

#### The `setup_project.sh` file

Here's the most important parts of `setup_project.sh`:

```bash title="utils/setup_project.sh"
...
rsync -ar ../sample_project/blog_project/ "$tmp_dir"
...
# Build a venv and install requirements.
python3 -m venv b_env
source b_env/bin/activate
pip install --no-index --find-links="$sd_root_dir/vendor/" -r requirements.txt

# Install local version of simple_deploy.
pip install -e "$sd_root_dir/"
...
# Make an initial commit.
git init
git add .
git commit -am "Initial commit."
git tag -am '' INITIAL_STATE

# Add simple_deploy to INSTALLED_APPS.
sed -i "" "s/# Third party apps./# Third party apps.\n    'simple_deploy',/" blog/settings.py
```

This file does a few important things, which last for the entire testing session:

- Copy the sample blog project to the location specified by `tmp_proj_dir`.
- Build a virtual environment.
- Make an editable install of `django-simple-deploy`. This means it installs from your local copy, not from PyPI. Any changes you make to your local version of `django-simple-deploy` are picked up by the unit tests.
- Make an initial commit of the test project, with the tag `INITIAL_STATE`.
- Add `simple_deploy` to the test project's `INSTALLED_APPS`.

#### The `run_simple_deploy()` fixture

This fixture has a module-level scope, and `autouse=True`. It is called once for each test module. Here's the function definition:

```python
@pytest.fixture(scope='module', autouse=True)
def run_simple_deploy(reset_test_project, tmp_project, request):
    ...
```

The important thing to note here is the inclusion of `reset_test_project` in the function's parameter list. When pytest sees this, it runs the `reset_test_project()` fixture before running the code in `run_simple_deploy()`.

#### The `reset_test_project()` fixture

This fixture just calls `reset_test_project.sh`, so let's look at that file:

```bash title="utils/reset_project.sh"
...
git reset --hard INITIAL_STATE
...
sed -i "" "s/# Third party apps./# Third party apps.\n    'simple_deploy',/" blog/settings.py
```

This file calls `git reset` using the tag `INITIAL_STATE`, and then adds `simple_deploy` back into the test project's `INSTALLED_APPS`.

This reset happens once per test module. It's good to note that this happens even if only one test module is being run. This fixture has no effect in that situation, but it also doesn't cause any harm to the test run.

#### Back to `run_simple_deploy()`

Now, back to `run_simple_deploy()`. Here's the most important parts:

```python
@pytest.fixture(scope='module', autouse=True)
def run_simple_deploy(reset_test_project, tmp_project, request):
    ...
    re_platform = r".*/unit_tests/platforms/(.*?)/.*"
    ...
    if m:
        platform = m.group(1)
    else:
        return
    ...
    cmd = f"sh utils/call_simple_deploy.sh -d {tmp_project} -p {platform} -s {sd_root_dir}"
    ...
```

This function uses a regular expression to find out which platform is currently being tested, which is assigned to `platform`. If there's no platform name, we don't need to run `simple_deploy`, so the function returns early. The function now runs `call_simple_deploy.sh`.

#### The `call_simple_deploy.sh` file

Here's `call_simple_deploy.sh`:

```bash title="utils/call_simple_deploy.sh"
if [ "$target_platform" = fly_io ]; then
    python manage.py simple_deploy --unit-testing --platform "$target_platform" --deployed-project-name my_blog_project
elif [ "$target_platform" = platform_sh ]; then
    python manage.py simple_deploy --unit-testing --platform "$target_platform" --deployed-project-name my_blog_project
elif [ "$target_platform" = heroku ]; then
    python manage.py simple_deploy --unit-testing --platform "$target_platform"
fi
```

This file calls `simple_deploy` with the `--unit-testing` flag, and any other parameters that are required for unit testing by the platform that's being tested.

We are finally finished with all of the fixtures, so we'll head back to one of the functions in `test_flyio_config.py`.

### A single test function

Here's one of the test functions that we can focus on:

```python title="unit_tests/platforms/fly_io/test_flyio_config.py"
...
import unit_tests.utils.ut_helper_functions as hf
...

def test_creates_dockerfile(tmp_project, pkg_manager):
    """Verify that dockerfile is created correctly."""
    if pkg_manager == "req_txt":
        hf.check_reference_file(tmp_project, 'dockerfile', 'fly_io')
    elif pkg_manager == "poetry":
        hf.check_reference_file(tmp_project, "dockerfile", "fly_io",
                reference_filename="poetry.dockerfile")
...
```

The test file imports the `utils/ut_helper_functions.py` module, which contains functions that are useful to test modules in different platform-specific directories.

 The function `test_creates_dockerfile()` has two arguments, `tmp_project` and `pkg_manager`. Here pytest takes the return value from the `tmp_project()` fixture, and assigns it to the variable `tmp_project`. This can be a little confusing; we have a fixture  in `conftest.py` called `tmp_project()`, but in the current test function `tmp_project` refers to the return value of `tmp_project()`. If this is confusing, keep in mind that **in this test function, `tmp_proj` is the path to the directory containing the test project.**

 The `pkg_manager` fixture tells us which depency management system is currently being tested: a bare `requirements.txt` file, Poetry, or Pipenv. We need to know this because each of these uses a slightly different `Dockerfile`.

In the body of the test function we check the current value of `pkg_manager` and then call `check_reference_file()`, which compares a file from the test project against the corresponding reference file. For `req_txt`, we make sure the `Dockerfile` that's created during the test run matches the reference `unit_tests/platforms/fly_io/reference_files/Dockerfile`. If your current local version of `django-simple-deploy` generates a `Dockerfile` for Fly.io deployments that doesn't match this file, you'll know. For Poetry, the reference filename doesn't match the generic generated filename, so we pass the optional `reference_filename` argument.

!!! note
    Reference filenames usually have a `platform_name.generic_filename.file_extension` pattern. It's really helpful to prepend the platform name so that we keep the original file extension, which enables syntax highlighting available when opening these files.

### Conclusion

That's a whole lot of setup work for a relatively short test function! But the advantage of all that setup work is that we can write hundreds, or thousands of small test functions without adding much to the setup work. Each test also runs three times: once for `req_txt`, once for `poetry`, and once for `pipenv`.

The rest of the test functions in `test_flyio_config.py` work in a similar way, except for `test_log_dir()`. That function inspects several aspects of the log directory, and the log file that should be found there.

!!! note
    The setup work will become more complex as we start to test multiple versions of Django, multiple versions of Python, and multiple OSes. But the overall approach described here shouldn't change significantly. We'll still have a bunch of setup work followed by a large number of smaller, specific test functions.


## Testing multiple platforms

What's the difference when we test multiple platforms? Not much; let's consider what happens when we test against two platforms in one test run:

```
(dsd_env)unit_tests $ pytest platforms/fly_io platforms/platform_sh
==================== test session starts ====================
platform darwin -- Python 3.10.0, pytest-7.1.2, pluggy-1.0.0
rootdir: django-simple-deploy
collected 13 items

platforms/fly_io/test_flyio_config.py .......
platforms/platform_sh/test_platformsh_config.py ......
==================== 13 passed in 16.07s ====================
```

Everything described above in [Testing a single platform](#testing-a-single-platform) happens in this test run as well. When all of the test functions in the first test module have been run, pytest moves on to the second test module.

In this case, that next test module is `test_platformsh_config.py`. Since the `tmp_project()` fixture has session-level scope, it doesn't run again. But all of the other fixtures have module-level scope, so they run again. Everything from [run_simple_deploy()](#the-run_simple_deploy-fixture) forward happens again, and at the end of all the setup work the test functions in `test_platformsh_config.py` run.

Note that the first test module doesn't finish running for about 12s (on my system). Much of that time is spent building the test project environment. Resetting the test project environment takes much less time, so the subsequent test modules finish much more quickly. It doesn't take much more time to test multiple platforms than it takes to test a single platform.

## Running platform-agnostic tests

The platform-agnostic tests are structured a little differently. Right now these are just a couple tests to verify that invalid CLI calls that don't target a specific platform are handled appropriately.

Here's the relevant parts of `test_invalid_cli_commands.py`:

```python hl_lines="29"
@pytest.fixture(scope="module", autouse=True)
def commit_test_project(reset_test_project, tmp_project):
    ...
    commit_msg = "Start with clean state before calling invalid command."
    cmd = f"sh utils/commit_test_project.sh {tmp_project}"
    ...

# --- Helper functions ---

def make_invalid_call(tmp_proj_dir, invalid_sd_command):
    ...
    cmd = f'sh utils/call_simple_deploy_invalid.sh {tmp_proj_dir}'
    ...

def check_project_unchanged(tmp_proj_dir, capfd):
    ...
    call_git_status(tmp_proj_dir)
    captured = capfd.readouterr()
    assert "On branch main\nnothing to commit, working tree clean" in captured.out

    call_git_log(tmp_proj_dir)
    captured = capfd.readouterr()
    assert "Start with clean state before calling invalid command." in captured.out

# --- Test modifications to settings.py ---

def test_bare_call(tmp_project, capfd):
    """Call simple_deploy with no arguments."""
    invalid_sd_command = "python manage.py simple_deploy"

    make_invalid_call(tmp_project, invalid_sd_command)
    captured = capfd.readouterr()

    assert "The --platform flag is required;" in captured.err
    assert "Please re-run the command with a --platform option specified." in captured.err
    assert "$ python manage.py simple_deploy --platform platform_sh" in captured.err
    check_project_unchanged(tmp_project, capfd)


def test_invalid_platform_call(tmp_project, capfd):
    ...

```

This test module has a single fixture with module-level scope, and `autouse=True`. This fixture is run once as soon as this test module is loaded. The fixture makes sure the test project is reset, and then makes a new commit. We want to verify that invalid commands don't change the project, and that's easiest to do with a clean git status.

Let's just look at the first test function, `test_bare_call()`. The highlighted line shows the exact command we want to test, `python manage.py simple_deploy`. This command is passed to the helper function `make_invalid_call()`, which calls `utils/call_simple_deploy_invalid.sh`. Unit tests require the `--unit-testing` flag, which the shell script adds in before making the call to `simple_deploy`. The end result is that our test functions get to contain the exact invalid commands that we expect end users to accidentally use.

The test function makes sure the user sees an appropriate error message, by examining the [captured terminal output](https://docs.pytest.org/en/7.2.x/how-to/capture-stdout-stderr.html). This is (mostly) the same output that end users will see. It also calls the helper function `check_project_unchanged()`, which makes sure there's a clean `git status` and that the last log message (returned by `git log -1 --pretty=oneline`) contains the same commit message that was used in the fixture at the top of this module.

## Running the entire test suite

Running the entire test suite puts together everything described above:

```
(dsd_env)unit_tests $ pytest
==================== test session starts ===============================
platform darwin -- Python 3.10.0, pytest-7.1.2, pluggy-1.0.0
rootdir: django-simple-deploy
collected 93 items

platform_agnostic_tests/test_invalid_cli_commands.py .........
platform_agnostic_tests/test_project_inspection.py sss
platform_agnostic_tests/test_valid_cli_commands.py ...
platforms/fly_io/test_flyio_config.py ...........................
platforms/heroku/test_heroku_config.py ...........................
platforms/platform_sh/test_platformsh_config.py ........................
==================== 90 passed, 3 skipped in 25.78s ====================
```

The test project is set up once, and reset for each test module that's run.

## Examining the modified test project

It can be really helpful to see exactly what a test run of `simple_deploy` does to the sample project. The original sample project is in `sample_project/`, and the modified version after running unit tests is stored wherever pytest [makes tmp directories](https://docs.pytest.org/en/latest/how-to/tmp_path.html#the-default-base-temporary-directory) on your system. That's typically a subfolder in your system's default temporary directory.

A quick way to find the exact path to the temp directory is to uncomment the following highlighted line in the `tmp_project()` fixture in `conftest.py`:

```python hl_lines="7"
@pytest.fixture(scope='session')
def tmp_project(tmp_path_factory):
    ...
    # To see where pytest creates the tmp_proj_dir, uncomment the following line.
    #   All tests will fail, but the AssertionError will show you the full path
    #   to tmp_proj_dir.
    # assert not tmp_proj_dir
    ...    

    return tmp_proj_dir
```

The next time you run the unit tests, this assert will fail, and the output will show you the path that was created:

```
(dsd_env)unit_tests $ pytest -x
...
>    assert not tmp_proj_dir
E    AssertionError: assert not PosixPath('/private/var/folders/md/4h9n_5l93qz76s_8sxkbnxpc0000gn/T/pytest-of-eric/pytest-274/blog_project0')
```

You can navigate to this folder in a terminal, and interact with the project in any way you want. It has a virtual environment, so you can activate it and run the project if you want.

!!! note
    The command `pytest -x` tells pytest to run the full test suite, but stop after the first failed test.

## Updating reference files

Examining the test project is an efficient way to update reference files. Say you've just updated the code for generating a Dockerfile for a specific package management system, ie Poetry. You can run the test suite with `pytest -x`, and it will fail at the test that checks the Dockerfile for that platform when Poetry is in use. You can examine the test project, open the Dockerfile, and verify that it was generated correctly for the sample project. If it is, copy this file into the `reference_files/` directory, and the tests should pass.

## Examining failures for parametrized tests

When a parametrized test fails, there's some important information in the output. For example, here's some sample output from a failed test run:

```
FAILED platforms/platform_sh/test_platformsh_config.py::test_platform_app_yaml_file[poetry] - AssertionError
```

This tells us that the test `test_platform_app_yaml_file` in `test_platformsh_config.py` failed, when the value of `pkg_manager` was `poetry`. So, we need to look at how `simple_deploy` configures the `.platform.app.yaml` file when Poetry is in use.

## Updating packages in `vendor/`

The sole purpose of the `vendor/` directory is to facilitate unit testing. To add a new package to the directory:

```
(dsd_env) $ pip download --dest vendor/ package_name
```

To upgrade all packages in `vendor/`:

```
$ rm -rf vendor/
$ pip download --dest vendor/ -r sample_project/blog_project/requirements.txt
```

## pytest references

- Fixtures
    - [About fixtures](https://docs.pytest.org/en/latest/explanation/fixtures.html)
    - [How to use fixtures](https://docs.pytest.org/en/latest/how-to/fixtures.html)
    - [Autouse fixtures](https://docs.pytest.org/en/latest/how-to/fixtures.html#autouse-fixtures-fixtures-you-don-t-have-to-request)
    - Fixture [scope](https://docs.pytest.org/en/latest/how-to/fixtures.html#scope-sharing-fixtures-across-classes-modules-packages-or-session)
    - Fixtures [reference](https://docs.pytest.org/en/latest/reference/fixtures.html#reference-fixtures)
    - [Parametrizing fixtures](https://docs.pytest.org/en/latest/how-to/fixtures.html#parametrizing-fixtures)
- Misc
    - [How to capture stdout/stderr output](https://docs.pytest.org/en/7.2.x/how-to/capture-stdout-stderr.html)
    - This is the [best discussion](https://stackoverflow.com/questions/34466027/in-pytest-what-is-the-use-of-conftest-py-files) I've found about `conftest.py`.