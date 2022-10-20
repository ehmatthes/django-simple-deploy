---
title: Making a New Release
---

Making a New Release
===

This documentation is as much for anyone else who begins to contribute to this project and is a good candidate for becoming a maintainer. A maintainer needs to  understand the technical tasks of merging PRs and managing issues, but also needs to be really clear about discussing, navigating, and defining the boundaries of this project.

Also, I know that Python packaging is often criticized as confusing because many different approaches have been tried over the years. I want to be really clear about the process used for creating and maintaining this package.


Building a package
---

- Use [build](https://pypa-build.readthedocs.io/en/stable/index.html) instead of [invoking setup.py directly](https://blog.ganssle.io/articles/2021/10/setup-py-deprecated.html).
- In root directory of this project, run `python -m build`.

Making a new release
---

- Commit all changes on your development branch. Make as many commits as you need to do the work you set out to do, but aim for a final atomic PR.
- Create a PR on GitHub.
- Accept the PR, using squash & merge.
- Pull changes to your local `main` branch: `git pull origin main`
- Bump the version number in `setup.cfg`.
- Make an entry in `changelog.md`.
- Commit this change: `git commit -am "Bumped version number, and updated changelog."`
- Delete everything in `dist/`: `rm -rf dist/`.
- Run `python -m build`, this recreates `dist/`.
- Tag the new release. While on the main branch:
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
(venv)$ ./integration_tests/test_deploy_process.sh -t pypi -p [fly_io|] -d [req_txt|poetry|pipenv]
```

Deleting branches
---

Delete the remote development branch, and then delete the local development branch.

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

- See [source](https://git-scm.com/book/en/v2/Git-Basics-Tagging) for more about tagging.
- See also [GH source about releases](https://docs.github.com/en/repositories/releasing-projects-on-github/managing-releases-in-a-repository)
