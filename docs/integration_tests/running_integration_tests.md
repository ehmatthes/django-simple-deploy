---
title: "Running Integration Tests"
hide:
    - footer
---

# Running Integration Tests

The integration tests were originally a pile of shell scripts that only worked on my macOS system. I'm most of the way through converting them to pure cross-platform Python. The original documentation is [here](https://github.com/ehmatthes/django-simple-deploy/blob/main/old_docs/integration_tests.md).

Here's the basic usage, until I can write this up more fully:

```sh
$ pytest integration_tests/platforms/heroku/test_deployment.py -s
```

The general form of this command is:

```sh
$ pytest integration_tests/platforms/<platform-name>/test_deployment.py -s
```

The `-s` flag when running integration tests, as there is a lot of output that gives you a sense of whether the deployment is on track or not. Each test takes 2-8 minutes to run, so having no output is problematic at this point. If you try to run integration tests without including `-s`, the test will exit with a reminder to include this flag.

Don't try to run the full suite of tests; these are currently designed to be run one at a time.

There are forms of the test command that tests against the current PyPI release, and tests the `--automate-all` flag as well. A full matrix would take a very long time, and create many live deployments. That is not feasible, or really necessary, at this stage.

## Testing specific package managers

You can run integration tests against a specific package manager. For example, here's how to test deployments on Fly.io for projects that use Poetry:

```sh
$ pytest integration_tests/platforms/fly_io/test_deployment.py --pkg-manager poetry -s
```

General form:

```sh
$ pytest integration_tests/platforms/<platform-name>/test_deployment.py --pkg-manager <req_txt|poetry|pipenv> -s
```

When this argument is omitted, the default package manager for testing is requirements.txt.

## Testing the `--automate-all` flag

To test deployments using `--automate-all`:

```sh
$ pytest integration_tests/platforms/<platform-name>/test_deployment.py --automate-all -s
```
