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

Testing
---

- Check for each platform's CLI when needed before running tests that depend on it.
- Check for poetry, and any other package manager, before running any tests that depend on it.
- Allow tests to be run for one specific package manager. Or exclude a package manager? See [#210](https://github.com/ehmatthes/django-simple-deploy/issues/210).

Documentation
---

- Add an `index.md` file for each main section. See [#139](https://github.com/ehmatthes/django-simple-deploy/issues/139).
- Update docs to clarify how this project can be useful to platform hosts (companies). See [#144](https://github.com/ehmatthes/django-simple-deploy/issues/144).

New platforms
---

- Support Railway. See [#75](https://github.com/ehmatthes/django-simple-deploy/issues/75).


Fly.io
---


Platform.sh
---


Heroku
---

- If not pushing from the main branch, state that explicitly. Consider confirming that's what user wants. State the branch name explicitly in the summary message. See [#5](https://github.com/ehmatthes/django-simple-deploy/issues/5).
- Reconsider Heroku support. People have lost confidence in Heroku in recent years, but it still keeps largely working. See [#91](https://github.com/ehmatthes/django-simple-deploy/issues/91).