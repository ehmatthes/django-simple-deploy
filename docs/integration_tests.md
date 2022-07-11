Integration Tests
===

I'm not new to testing in general, but I'm a little new to testing something like a deployment library. The main integration test starts with a Django project that's ready for deployment, but not configured for deployment. Then it needs to be configured, deployed, and the deployed app needs to be tested. Some of these steps are easier to write outside of Python, I believe.

My current get-something-up-and-running approach is to start in Bash to do the setup and deployment steps, and then call a Python script to test the functionality of the deployed app.

If you want to run these tests, you'll need an account on the platform you're testing against. The test will create an app under your account, and it should prompt you to destroy that app if the test runs successfully. If the test script fails, it may exit before destroying some deployed resources. You should  verify that the app and any related resources were actually destroyed, especially if these resources will accrue charges on your account.

Table of Contents
---

- [Running the integration tests](#running-the-integration-tests)
- [Actual steps](#actual-steps)
- [Testing the latest PyPI release](#testing-the-latest-pypi-release)
- [Other testing options](#other-testing-options)
    - [Testing against Poetry](#testing-against-poetry)
- [Testing other platforms](#testing-other-platforms)
- [Don't modify testing script while running](#dont-modify-testing-script-while-running)

Running the integration tests
---

The tests run against your local version of this project. So if you want to work on this project:
- Clone the repository, and make a virtual environment from the `requirements.txt` file.
- Make any changes to the project you're interested in.
- Run the tests: `$ ./integration_tests/test_deploy_process.sh`

Actual steps
---

The actual steps to start developing by running the integration test should look like this. Call your virtual environment `dsd_env`, so it matches what's in `.gitignore`:

```
$ git clone https://github.com/ehmatthes/django-simple-deploy.git
$ cd django-simple-deploy
$ python3 -m venv dsd_env
$ source dsd_env/bin/activate
(dsd_env)$ pip install --upgrade pip
(dsd_env)$ pip install requirements.txt
(dsd_env)$ ./integration_tests/test_deploy_process.sh
```

Testing the latest PyPI release
---

To test the latest release on PyPI instead of your local version of the project, use the `-t pypi` argument:

```
(dsd_env)$ ./integration_tests/test_deploy_process.sh -t pypi
```

Other testing options
---

Here are all the flags and options for each flag. The first option listed for each flag is the default:

```
./integration_tests/test_deploy_process.sh -t [development_version|pypi] -d [req_txt|poetry|pipenv] -p [heroku] -o [automate_all]
```

- `-t`: Target for testing.
    - `development_version`, `pypi`
- `-d`: Dependency management approach that's being tested.
    - `req_txt`, `poetry`, `pipenv`
- `-p`: Platform to push to.
    - `heroku`
- `-o`: Options for the simple_deploy run.
    - `automate_all`

### Testing against Poetry

Testing poetry has been problematic for me due to caching issues. If you see errors about installing requirements to the temporary environment created during the tests, try clearing the cache manually before running the tests:

```
$ poetry cache clear --all pypi
$ ./integration_tests/autoconfigure_deploy_test -d poetry
```

Example: Test the `--automate-all` approach using poetry:
```
$ ./integration_tests/test_deploy_process.sh -o automate_all -d poetry
```

Testing other platforms
---

- The script tests Heroku deployments by default.
- The `-p` flag allows testing against other platforms.
- This is currently identical to running without the `-p` flag:
```
$ ./integration_tests/test_deploy_process.sh -p heroku
```

Don't modify testing script while running
---

If you modify the `test_deploy_process.sh` file while the test is running, it will try to load your changes during the current test run. This will almost certainly fail. If it happens, remember to destroy the tmp files manually, and make sure you destroy any apps that were created on your account as well.