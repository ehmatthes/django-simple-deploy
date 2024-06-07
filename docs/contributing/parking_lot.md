---
title: Parking Lot
hide:
    - footer
---

# Parking Lot

This is a place to dump ideas that aren't yet actionable. This document exists to keep from cluttering up issues with tasks that aren't really closable in a short timeframe.

General ideas
---

- Write a user-friendly deployment summary. See [#51](https://github.com/ehmatthes/django-simple-deploy/issues/51), and [#160](https://github.com/ehmatthes/django-simple-deploy/issues/160).
- Support one platform with an API-based workflow.
    - This will help clarify what kinds of utility functions should be included in core, for consistency of implementation, workflow, and testing.
- Support nested project directory structure, ie projects created from `startproject <project-name>`, not `startproject <project-name> .` (with a dot). See [#55](https://github.com/ehmatthes/django-simple-deploy/issues/55).
- Consider using Rich for nicer terminal output. See [#70](https://github.com/ehmatthes/django-simple-deploy/issues/70).
- Implement a `--check` flag. This would inspect the system and project, and report any identifiable issues that would prevent deployment. It would not make any changes to the project. May do platform-specific validation as well? See [#80](https://github.com/ehmatthes/django-simple-deploy/issues/80).
- Remove `old_docs/` directory. See [#138](https://github.com/ehmatthes/django-simple-deploy/issues/138).
- Support deploying project from the Django Girls tutorial. See [#82](https://github.com/ehmatthes/django-simple-deploy/issues/82).
- Support PDM. See [#137](https://github.com/ehmatthes/django-simple-deploy/issues/137).
- Look at settings in [django-production](https://github.com/lincolnloop/django-production). See [#147](https://github.com/ehmatthes/django-simple-deploy/issues/147).
- Set up CI. See [#148](https://github.com/ehmatthes/django-simple-deploy/issues/148).
- Identify current branch? Warn about non-main branch? See [#150](https://github.com/ehmatthes/django-simple-deploy/issues/150).
- Note talks, articles, discussion etc related to this project. See [#208](https://github.com/ehmatthes/django-simple-deploy/issues/208).
- Consider a stability policy. See [#214](https://github.com/ehmatthes/django-simple-deploy/issues/214).
- Consider a `--dry-run` feature. See [#247](https://github.com/ehmatthes/django-simple-deploy/issues/247).
- Revisit `git status` check in simple_deploy.py. See [#261](https://github.com/ehmatthes/django-simple-deploy/issues/261).
- Document use of development tools such as reset_project.py. See [#264](https://github.com/ehmatthes/django-simple-deploy/issues/264).
- Look at consistency of platform messages. See [#270](https://github.com/ehmatthes/django-simple-deploy/issues/264).
- Consider a tagline. [#284](https://github.com/ehmatthes/django-simple-deploy/issues/284).
- Consider pyupgrade for finding old Python idioms that are no longer needed. See [#299](https://github.com/ehmatthes/django-simple-deploy/issues/299).
- Try simple_deploy with a micro framework such as [django-singlefile](https://github.com/andrewgodwin/django-singlefile) or [nanodjango](https://github.com/radiac/nanodjango).
- Should the project support Poetry?
    - Poetry seems to be well-respected for developing libraries, but I don't know that anyone is really using it to manage dependencies for Django projects. If not, there's no reason to support it in this project.
    - Perhaps support it, but dial back some of the specificity of tests? Poetry is resolving at a finer grain size than we need to pay attention to?
    - I believe poetry does not conform to emerging standards for specifying Python dependencies. How much of a burden is it to support poetry? Perhaps moderate support, in the sense of exporting to requirements.txt?
- There are some interesting notes in [#238](https://github.com/ehmatthes/django-simple-deploy/issues/238).
- Add `black` to CI.

Testing
---

- Check for each platform's CLI when needed before running tests that depend on it.
- Check for poetry, and any other package manager, before running any tests that depend on it.
- Allow tests to be run for one specific package manager. Or exclude a package manager? See [#270](https://github.com/ehmatthes/django-simple-deploy/issues/270).
- Add a `--show-diff` argument to unit tests/ integration tests. See [#271](https://github.com/ehmatthes/django-simple-deploy/issues/271).
- Consider using `uv` in place of `pip`, at least when testing. See [#291](https://github.com/ehmatthes/django-simple-deploy/issues/291).
- Refine testing. See [#296](https://github.com/ehmatthes/django-simple-deploy/issues/296), and any open tasks in [#285](https://github.com/ehmatthes/django-simple-deploy/issues/285).
- Move `build_dev_env.py` from `e2e_tests/utils/` to `developer_resources/`. See [#245](https://github.com/ehmatthes/django-simple-deploy/issues/245).

Documentation
---

- Add an `index.md` file for each main section. See [#139](https://github.com/ehmatthes/django-simple-deploy/issues/139).
- Update docs to clarify how this project can be useful to platform hosts (companies). See [#144](https://github.com/ehmatthes/django-simple-deploy/issues/144).

New platforms
---

- Support Railway. See [#75](https://github.com/ehmatthes/django-simple-deploy/issues/75).


Fly.io
---

- Simplify approach to checking for db. See [#297](https://github.com/ehmatthes/django-simple-deploy/issues/297).

Platform.sh
---

- Update runtime to Python 3.12.
- The method `_validate_platform()` makes sure the user is authenticated through the CLI. I believe we can remove some checks for authentication in subsequent CLI calls, as in `_get_org_name()`.


Heroku
---

- If not pushing from the main branch, state that explicitly. Consider confirming that's what user wants. State the branch name explicitly in the summary message. See [#5](https://github.com/ehmatthes/django-simple-deploy/issues/5).
- Reconsider Heroku support. People have lost confidence in Heroku in recent years, but it still keeps largely working. See [#91](https://github.com/ehmatthes/django-simple-deploy/issues/91).


Windows
---

- Cloning to a Windows VM automatically started a development server for the sample project?!

```cmd
C:\Users\eric>git clone https://github.com/ehmatthes/django-simple-deploy.git
Cloning into 'django-simple-deploy'...
remote: Enumerating objects: 4832, done.
remote: Counting objects: 100% (1000/1000), done.
remote: Compressing objects: 100% (528/528), done.
remote: Total 4832 (delta 635), reused 683 (delta 440), pack-reused 3832
Receiving objects: 100% (4832/4832), 17.16 MiB | 17.14 MiB/s, done.
Resolving deltas: 100% (2781/2781), done.

C:\Users\eric>C:\Users\eric\django-simple-deploy\simple_deploy\apps.py changed, reloading.
Watching for file changes with StatReloader
Performing system checks...

System check identified no issues (0 silenced).
May 31, 2024 - 06:32:02
Django version 5.0.6, using settings 'blog.settings'
Starting development server at http://127.0.0.1:8008/
Quit the server with CTRL-BREAK.
```