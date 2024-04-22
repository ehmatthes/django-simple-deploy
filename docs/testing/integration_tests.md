---
title: Integration Tests
hide:
    - footer
---

The main goal of integration tests is to run `simple_deploy` against a test project, and verify that it makes appropriate changes to the project. This happens *without* any network calls, or use of external resources.

Integration tests include some other tests as well, such as making sure that invalid calls generate appropriate error messages.

The challenge
---

The challenge of writing integration tests is that `simple_deploy` is a standalone management command. The project has no settings of its own. There are no apps, no manage.py file, or anything like that.

My current approach to integration testing is to copy the example project to a temp dir, and then run simple_deploy against that temp project. Including the `--integration-testing` flag when running `simple_deploy` prevents any network calls from being made.

It's also a challenge that the `simple_deploy` command needs to be called repeatedly against the same temp project. The test suite issues Git commands to manage the state of the temp project during the test run.

Running integration tests
---

```sh
(dsd_env)django-simple-deploy$ pytest tests/integration_tests
```

Integration tests require that Poetry and Pipenv are installed. The tests call simple deploy against a version using each of these package managers, once for each supported platform. It should tell you gracefully if one of these requirements is not met.

### Testing a single platform

You can easily run tests against a single platform:

```sh
(dsd_env)django-simple-deploy$ pytest tests/integration_tests/platforms/fly_io
```

### Consider using the `-s` flag

```sh
(dsd_env)django-simple-deploy$ pytest tests/integration_tests -s
```

If you include the `-s` flag, you'll see a whole bunch of output that can be helpful for troubleshooting. For example you'll see output related to creating a copy of the project in a temp environment, you'll see all the versions of the `simple_deploy` command that are being run, and you'll see the locations of the test projects that are being set up.

Running unit and integration tests together
---

Unit tests and integration tests can be run together:

```sh
(dsd_env)django-simple-deploy$ pytest
```

The bare `pytest` command will run all unit and integration tests. It will *not* run end-to-end tests; those tests need to be run explicitly.

Tests as a development tool
---

The integration tests are quite useful for ongoing development work. For example, consider the following test command:

```sh
(dsd_env)django-simple-deploy$ % pytest tests/integration_tests/platforms/fly_io -k req_txt -s
```

This will create a temp project that uses requirements.txt to manage dependencies, and run a slight variation of `python manage.py simple_deploy --platform fly_io` against the project.

The `-s` flag will show you exactly where that temp project is. You can open a terminal, cd to that directory, activate the project's virtual environment, and poke around as much as you need to. You can modify simple_deploy, and run the command again. You can run `git status` and `git log`, and reset the projet to an earlier state, and run simple_deploy as many times as you want.

This is often *much* easier than just working in a test project that you set up manually.

### Look at the logs

If you're troubleshooting a failed test, run `pytest tests/integration_tests -lf -s` to rerun the last failed test. Go to the temp project directory, and look at th log that was generated in `simple_deploy_logs/`. That log file will often tell you exactly where the command failed. Again, you can use Git to reset the test project, and run `simple_deploy` again to recreate the issue manually.

### Experimental feature

On macOS, you can run the following command:

```sh
(dsd_env)django-simple-deploy$ pytest tests/integration_tests -x --open-test-project
```

This will stop at the first failed test, and open a new terminal tab at the test project's location. It runs `git status` and `git log --pretty=oneline` automatically, and invites you to poke around the project. This is a really helpful feature, that I'd like to refine.

Maintaining integration tests
---

### Updating reference files

Examining the test project is an efficient way to update reference files. Say you've just updated the code for generating a Dockerfile for a specific package management system, ie Poetry. You can run the test suite with `pytest -x`, and it will fail at the test that checks the Dockerfile for that platform when Poetry is in use. You can examine the test project, open the Dockerfile, and verify that it was generated correctly for the sample project. If it is, copy this file into the `reference_files/` directory, and the tests should pass.

### Updating packages in `vendor/`

The main purpose of the `vendor/` directory is to facilitate integration testing. To add a new package to the directory:

```sh
(dsd_env) $ pip download --dest vendor/ package_name
```

To upgrade all packages in `vendor/`:

```sh
$ rm -rf vendor/
$ pip download --dest vendor/ -r sample_project/blog_project/requirements.txt
```