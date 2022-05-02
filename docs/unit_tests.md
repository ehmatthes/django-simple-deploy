Unit Tests
===

Testing this project is interesting because it's a Django project whose sole purpose is to act on a separate Django project. Currently, unit testing takes the following approach:
- Call a bash script to create a temporary instance of the sample blog project;
- Install the local development version of the django-simple-deploy project to this test instance;
- Run the configuration-only version of simple_deploy against the test instance, using the `--local-test` flag to avoid any network calls such as `heroku apps:info`;
- Make assertions about the changes that should have been made to the test instance.

This all takes about 13 seconds currently; most of that time is spent building the virtual environment for the test instance of the sample project. The environment is all built from the vendor/ directory. The unit tests do not make any network calls, although this is not enforced.

There is some testing cruft written into the main project. For example, we check for the `--local-test` flag, and skip some network calls such as setting Heroku environment variables.

If you have suggestions for how to improve the overall structure of these unit tests, or speed them up in any way, please open an issue or send an email and I will be happy to hear your thoughts. I'm sure someone with deeper Django, deployment, and Pytest experience than I have could improve on what I have started. That said, these tests are a good start at making sure ongoing development does not break current behavior.

Table of Contents
---

- [Running unit tests](#running-unit-tests)
- [Updating packages in vendor/](#updating-packages-in-vendor)
- [Useful notes](#useful-notes)
- [Unit testing roadmap](#unit-testing-roadmap)

Running unit tests
---

To run the unit tests:

```
(dsd_env) django-simple-deploy $ cd unit_tests
(dsd_env) django-simple-deploy/unit_tests $ pytest
```

Don't call pytest from the root directory, or pytest will try to run the [integration tests](integration_tests.md) as well.

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

Unit testing roadmap
---

Currently, unit testing only covers the default Heroku configuration work. The approach to adding more coverage is probably this:
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