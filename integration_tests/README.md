Integration Tests
===

I'm not new to testing in general, but I'm a little new to testing something like a deployment library. The main integration test involves pulling in a Django project that's ready for deployment, but not configured for deployment. Then it needs to be configured, deployed, and the deployed app needs to be tested. Some of these steps are easier to write outside of Python, I believe.

My current get-something-up-and-running approach is to start in Bash to do the setup and deployment steps, and then call a Python script to test the functionality of the deployed app.

If you want to run these tests, you'll need a Heroku account. The test will create an app in your account, and it should destroy that app if the test runs successfully. If the Bash script finishes running, even though some errors occur, the Heroku app should be destroyed. You should probably verify that the app was actually destroyed, especially if having another app deployed will accrue charges for you.

Running the integration tests
---

The tests run against the latest pushed version of the current branch you're working in. So if you want to work on this project:
- Check out a new branch.
- Commit your changes and push your branch.
- Run the tests.

Run the test file:
- `$ cd integration_tests`
- `$ ./autoconfigure_deploy_test.sh`

I believe this also works from the root folder:
- `$ ./integration_tests/autoconfigure_deploy_test.sh`

Note: I believe this approach works for anyone, on any fork. If it's not working for you, please open an issue.
