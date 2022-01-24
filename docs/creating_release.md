Creating a Release
===

I'm not new to Python or Django, but I am new to creating and maintaining a package. So, this documentation is as much for me as a new package maintainer as it is for anyone else. Also, I know that Python packaging is often criticized as confusing because many different approaches have been tried over the years. I want to be really clear about the process used for creating and maintaining this package.


Building a package
---

- Use [build](https://pypa-build.readthedocs.io/en/stable/index.html) instead of [invoking setup.py directly](https://blog.ganssle.io/articles/2021/10/setup-py-deprecated.html).
- In root directory of this project, run `python -m build`.

Making a new release
---

- Make sure version number has been bumped in `setup.cfg`.
- Make an entry in changelog.md.
- Commit all changes on development branch.
- Create a PR on GitHub, accept the PR, and pull changes to main locally.
- Delete everything in dist/.
- Run `python -m build`
- Push to test.pypi with twine:
```
(venv)$ python -m twine upload --repository testpypi dist/* --username __token__ --password [testpypi_access_token]`
```
- Push to PyPI:
```
(venv)$ python -m twine upload dist/*
```
- Test the released package:
```
(venv)$ ./integration_tests/test_deploy_process.sh -t pypi -d [req_txt|poetry|pipenv]
```

Deleting branches
---

I always forget this, so put it here. Delete on the remote, and then delete locally.

```
$ git push origin -d feature_branch
$ git branch -d feature_branch
```

Testing locally (non-automated)
---

- We assume you have a copy of this repository in your home folder.
- In a Django project that hasn't been deployed or configured for deployment, do the following:
  - $ python -m pip install -e ~/projects/django-simple-deploy
  - Add `simple_deploy` to `INSTALLED_APPS`
  - $ heroku create
  - $ python manage.py simple_deploy
  - $ git add .
  - $ git commit -am "Configured for deployment."
  - $ git push heroku main
  - $ heroku run python manage.py migrate
  - $ heroku open

