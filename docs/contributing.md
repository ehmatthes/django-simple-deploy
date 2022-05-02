Contributing
===

First of all, thank you for your interest in contributing to this project. There are a number of ways you can get started:
- [Run a demo](#run-a-demo)
  - Download a simple Django blog project, and use django-simple-deploy to deploy the project.
- [Run the unit tests](#run-the-unit-tests)
  - Set up a development environment for this project, and run the unit tests. This does not involve deployment to a platform.
- [Run the integration tests](#run-the-integration-tests)
  - Set up a development environment, and run the integration tests. This requires an account on the platform you want to test against.    
- Open an issue
  - Open an [issue](https://github.com/ehmatthes/django-simple-deploy/issues), and share your thoughts about this project. Feel free to use issues for asking questions, sharing feedback, or reporting bugs.
- Code of Conduct
  - This project has adopted the [Contributor Covenant](https://www.contributor-covenant.org/version/2/1/code_of_conduct/) as a [Code of Conduct](code_of_conduct.md).

If you want to begin contributing to the project, start with the section about running unit tests.

Run a demo
--

One of the best ways to get started is to use django-simple-deploy to deploy a working Django project. This requires an active account on the platform you want to use, such as Heroku or Azure.

- Clone the [demo blog project](https://github.com/ehmatthes/dsd_blog) that's used for testing django-simple-deploy.
  - `$ git clone https://github.com/ehmatthes/dsd_blog.git`
  - `$ cd dsd_blog/`
- Create a virtual environment, install the requirements, and migrate the project. (Call your virtual environment `b_env`, so it matches what's listed in `.gitignore`.)
```
$ python3 -m venv b_env
$ source b_env/bin/activate
(b_env)$ pip install -r requirements.txt
(b_env)$ python manage.py migrate
```
- Run the project locally.
  - `(b_env)$ python manage.py runserver`
  - Play around with the project, and verify that it works on your system.
- Deploy the project using django-simple-deploy:
  - `pip install django-simple-deploy`
  - Add `simple_deploy` to `INSTALLED_APPS`.
  - Run the deployment command: `python manage.py simple_deploy --automate-all --platform heroku`
  - You should see a bunch of output, and you should see a live version of the project appear in a new browser tab.
- Cleanup
  - If the deployment process did not work, please [open an issue](https://github.com/ehmatthes/django-simple-deploy/issues).
  - If you have any questions or feedback about the process, please open an issue as well.
  - You probably want to destroy the test app. You can either use your platform's dashboard to do this, or use a cli command. For example `heroku apps:destroy app_name`.

Run the unit tests
---

Running the unit tests is the best way to start contributing to the project. This way you know your development environment is set up correctly. First, clone this repo and build the virtual environment for the project. (Call your virtual environment `dsd_env`, so it matches what's in `.gitignore`.):
```
$ git clone https://github.com/ehmatthes/django-simple-deploy.git
$ cd django-simple-deploy
$ python3 -m venv dsd_env
$ source dsd_env/bin/activate
(dsd_env)$ pip install --upgrade pip
(dsd_env)$ pip install -r requirements.txt
```

Now you should be able to run the unit tests. The unit tests will copy the demo blog project from `sample_tests/` to a temporary directory, and run the tests against that demo project. Currently (5/2022), the tests take about 13 seconds on my system. To run the unit tests:

```
(dsd_env) django-simple-deploy $ cd unit_tests
(dsd_env) django-simple-deploy/unit_tests $ pytest
```

Don't call pytest from the root directory, or pytest will try to run the [integration tests](integration_tests.md) as well.

For more information, see the full [unit tests](unit_tests.md) documentation.

Run the integration tests
---

For now, see the full documentation for [integration tests](integration_tests.md).
