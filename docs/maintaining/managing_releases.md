---
title: Managing Releases
---

Managing Releases
===



Making a new release
---

- Make sure you are on the main branch, and you have pulled all recently merged changes: `git pull origin main`
- Bump the version number in `setup.cfg`
- Make an entry in `changelog.md`
- Commit this change: `git commit -am "Bumped version number, and updated changelog."`
- Push this change directly to main: `git push origin main`
- Delete everything in `dist/`: `rm -rf dist/`
- Run `python -m build`, which recreates `dist/`
- Tag the new release:
    - `$ git tag vA.B.C`
    - `$ git push origin vA.B.C`

- Push to PyPI:
```
(venv)$ python -m twine upload dist/*
```

- View on PyPI:
[https://pypi.org/project/django-simple-deploy/](https://pypi.org/project/django-simple-deploy/)

- Test the released package:
```
$ pytest tests/e2e_tests --platform <platform-name> --pypi -s
```

    - Sometimes there's a stale cache that causes the previous release to be installed. If you don't check this version, you won't know whether the new release actually works. In the test output, verify that the new version was installed. Look for something like this:

```sh
$ pytest tests/e2e_tests --platform fly_io --pypi -s
Temp project directory: ...
...
Collecting django-simple-deploy
  Downloading django_simple_deploy-0.6.2-py3-none-any.whl.metadata
...
Successfully installed Django-5.0.6 ... django-simple-deploy-0.6.2 ...
...
```

Deleting branches
---

Delete the remote and local development branches:

```
$ git push origin -d feature_branch
$ git branch -d feature_branch
```

Deleting tags
---

If needed:

```
$ git tag -d vA.B.C
```

- See [Git docs](https://git-scm.com/book/en/v2/Git-Basics-Tagging) for more about tagging.
- See also [GH docs about releases](https://docs.github.com/en/repositories/releasing-projects-on-github/managing-releases-in-a-repository).
