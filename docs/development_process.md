Development process
===

Developing an app that focuses on deployment involves a different kind of workflow than I have used on other projects. Often times the work needs to be done in conjunction with a sample project that exists outside this main directory.

Quick start
---

- Make a sample Django project in a location outside this repository.
  - It needs to be managed by Git, and it's much easier to not deal with a repo-in-a-repo, or submodules.
  - I'm using a copy of the [Learning Log project](https://github.com/ehmatthes/learning_log_heroku_test) from Python Crash Course, but long term we should make a standard generic blog app specifically for development and testing work on this project.
- In that project, install django-simple-deploy from your local version of this repository. If this repo is in ~/projects/django-simple-deploy/, that would look like this:
```
(venv)$ pip install -e ~/projects/django-simple-deploy/
```
- This is an "editable install". It means any time you make changes in the local simple-deploy repository, they will be pulled into the sample project as well.


Developing with Pipenv
---

I don't normally use Pipenv, so I need some notes for developing for Pipenv support.  

- I have a test project that uses Pipenv. It's core aspect is to have a Pipfile.
- It should follow the same process described above, starting from just a Pipfile, and maybe with a Pipfile.lock:
```
$ python3 -m pipenv install
$ python3 -m pipenv install -e ~/projects/django-simple-deploy/
```
- To activate the virtual environment created by Pipenv, and then you can run ie management commands:
```
$ python3 -m pipenv shell
(venv_path)$ python manage.py check
```
- To deactivate the environment, use `exit`; don't use `deactivate`.
