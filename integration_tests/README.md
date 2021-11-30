Integration Tests
===

I'm not new to testing in general, but I'm a little new to testing something like a deployment library. The main integration test involves pulling in a Django project that's ready for deployment, but not configured for deployment. Then it needs to be configured, deployed, and the deployed app needs to be tested. Some of these steps are easier to write outside of Python, I believe.

My current get-something-up-and-running approach is to start in Bash to do the setup and deployment steps, and then call a Python script to test the functionality of the deployed app.

If you want to run these tests, you'll need a Heroku account. The test will create an app in your account, and it should destroy that app if the test runs successfully. If the Bash script finishes running, even though some errors occur, the Heroku app should be destroyed. You should probably verify that the app was actually destroyed, especially if having another app deployed will accrue charges for you.

Running the integration tests
---

The tests run against the latest pushed version of the current branch you're working in. So if you want to work on this project:
- Clone the repository, and make a virtual environment from the `requirements.txt` file.
- Check out a new branch.
- Commit your changes and push your branch.
- Run the tests.

Run the test file:
- `$ cd integration_tests`
- `$ ./autoconfigure_deploy_test.sh`

I believe this also works from the root folder:
- `$ ./integration_tests/autoconfigure_deploy_test.sh`

Note: I believe this approach works for anyone, on any fork. If it's not working for you, please open an issue.

Actual steps
---

The actual steps to start developing by running the integration test should look like this:

```
$ git clone https://github.com/ehmatthes/django-simple-deploy.git
$ cd django-simple-deploy
$ python3 -m venv venv
(venv)$ pip install --upgrade pip
(venv)$ pip install requirements.txt
(venv)$ ./integration_tests/autoconfigure_deploy_test.sh
```

Testing the latest PyPI release
---

To test the latest release on PyPI instead of the current branch, use the `test_pypi_release` argument:

```
(venv)$ ./integration_tests/autoconfigure_deploy_test.sh test_pypi_release
```

Testing options
---

```
./integration_tests/autoconfigure_deploy_test.sh -t [pypi|current_branch] -d [req_txt|poetry|pipenv] -o [automate_all] -p [heroku|azure]
```

Testing poetry has been problematic for me due to caching issues. If you see errors about installing requirements to the temporary environment created during the tests, try clearing the cache manually before running the tests:

```
$ poetry cache clear --all pypi
$ ./integration_tests/autoconfigure_deploy_test -d poetry
```

Example: Test the `--automate-all` approach using poetry:
```
$ ./integration_tests/autoconfigure_deploy_test.sh -o automate_all -d poetry
```

Testing other platforms
---

- The script tests Heroku deployments by default.
- The `-p` flag will allow testing of other platforms.
- This is currently identical to running without the `-p` flag:
```
$ ./integration_tests/autoconfigure_deploy_test.sh -o automate_all -p heroku
```

Don't modify testing script while running
---

If you modify the autoconfigure_deploy_test.sh file while the test is running, it will try to load your changes during the current test run. This will almost certainly fail. If it happens, remember to destroy the tmp files manually, and make sure you destroy any apps that were created on your account as well.