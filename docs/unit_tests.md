Unit Tests
===

Testing this project is interesting because it's a Django project whose sole purpose is to act on a separate Django project. Currently, unit testing takes the following approach:

- Call a bash script to create a temporary instance of the sample blog project;
- Install the local development version of the django-simple-deploy project to this test instance;
- Run the configuration-only version of simple_deploy against the test instance, using the `--local-test` flag to avoid any network calls such as `heroku apps:info`;
- Make assertions about the changes that should have been made to the test instance of the sample project.

This all takes about 13 seconds currently, for each platform that's supported. Most of that time is spent building the virtual environment for the test instance of the sample project. The environment is all built from the vendor/ directory. The unit tests do not make any network calls, although this is not enforced.

There is some testing cruft written into the main project. For example, we check for the `--local-test` flag, and skip some network calls such as setting Heroku environment variables.

If you have suggestions for how to improve the overall structure of these unit tests, or speed them up in any way, please open an issue or send an email and I will be happy to hear your thoughts. I'm sure someone with deeper Django, deployment, and pytest experience than I have could improve on what I have started. That said, these tests are a good start at making sure ongoing development does not break current behavior.

Table of Contents
---

- [Running unit tests](#running-unit-tests)
	- [Running tests for a single platform](#running-tests-for-a-single-platform)
- [Examining the modified test project](#examining-the-modified-test-project)
- [Updating packages in vendor/](#updating-packages-in-vendor)
- [Useful notes](#useful-notes)
- [Efficiency considerations](#efficiency-considerations)

Running unit tests
---

To run the unit tests:

```
(dsd_env) django-simple-deploy $ cd unit_tests
(dsd_env) django-simple-deploy/unit_tests $ pytest
```

This will run all of the tests, for all currently supported platforms. As of this writing there are two supported platforms, Heroku and Platform.sh. In total this takes almost 30 seconds to run the full set of tests. Adding more platforms will significantly lengthen the test runs; adding more tests to an existing platform does not significantly affect the efficiency of tests.

Don't call pytest from the root directory, or pytest will try to run the [integration tests](integration_tests.md) as well.

### Running tests for a single platform

To run tests for a single platform, call `pytest` with the test file for the platform you're working on:

```
(dsd_env) django-simple-deploy/unit_tests $ pytest test_heroku_config.py
```

This will run only the tests for a single platform, which currently takes about 13-15 seconds.

Examining the modified test project
---

It can be really helpful to see exactly what the test run of `simple_deploy` does to the sample project. The original sample project is in `sample_project/`, and the modified version after running unit tests is stored wherever pytest [makes tmp directories](https://docs.pytest.org/en/7.1.x/how-to/tmp_path.html#the-default-base-temporary-directory) on your system. That's typically a subfolder in your system's default temporary directory.

A quick way to find the exact path to the temp directory is to modify `conftest.py`. Make an assert statement about the temporary directory that will fail:

```python
tmp_proj_dir = tmpdir_factory.mktemp('blog_project')
assert not tmp_proj_dir
```

The next time you run the unit tests, this assert will fail, and the output will show you the path that was created:

```
(dsd_env) $ pytest
...
>       assert not tmp_proj_dir
E       AssertionError: assert not local('/private/var/folders/md/4h9n_5l93qz76s_8sxkbnxpc0000gn/T/pytest-of-eric/pytest-73/blog_project0')
```

It can be helpful to see the modified project when developing and maintaining unit tests, and also when trying to see how the project is modified when targeting a specific platform.

Updating packages in vendor/
---

The sole purpose of the vendor/ directory is to facilitate unit testing. To add a new package to the directory:

```
(dsd_env) $ pip download --dest vendor/ package_name
```

I haven't upgraded a package in vendor/ yet, but it should be straightforward. If nothing else, delete the existing package resource and run the above command again.

Useful notes
---

See [#62](https://github.com/ehmatthes/django-simple-deploy/issues/62) for initial working notes about setting up unit testing.

Efficiency considerations
---

Currently, testing a single platform takes just under 15 seconds. Each new platform that's tested takes an additional ~15 seconds, because most of that time is spent creating a temporary version of the sample project to test against. This setup includes building a virtual environment from the vendor/ directory.

It should be possible to use one instance of the test project for all platforms being tested:

- Run a `git reset --hard` in the test instance repository to bring the test instance back to the state before running simple_deploy;
    - First pass at this, related to simplifying `ALLOWED_HOSTS` setting, adds a tag `INITIAL_STATE` to the initial commit. Then a new `modify_allowed_hosts.sh` file resets back to this tagged commit, modifies the project, and runs simple_deploy again. See unit_tests/modify_allowed_hosts.sh.
- Modify the test instance of the project in order to test a different pathway;
- Run simple_deploy again;
- Run a new series of tests.

To do this, we'll probably need a main test file that specifies an order for these tests, and also allows the developer to select which unit tests to run. We probably want to be able to do something like the following:

```
(dsd_env) django-simple-deploy/unit_tests $ pytest --platform heroku
```

Pytest should offer a number of ways to do this efficiently.

However, I'm not sure all of that is worthwhile; it may be beneficial to create a new venv and sample project for each platform tested:

- Reusing the project instance relies on undoing everything `simple_deploy` did. This isn't as straightforward as issuing a `git reset --hard` command. We also need to destroy new resources, such as the logs/ directory.
- This is a complex enough project that there might be other impacts of reusing the test project; starting with a fresh project instance for each platform gives more confidence that tests are covering everything appropriately.
- During most development work, you only need to run the tests against the current platform you're targeting. If you're only modifying parts of simple_deploy that target a specific platform, there's no reason to run tests against all other platforms until you're ready to merge.