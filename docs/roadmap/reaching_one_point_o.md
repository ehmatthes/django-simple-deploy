---
title: "Roadmap to 1.0"
hide:
    - footer
---

# Roadmap to 1.0

This page lays out the items that need to be completed before we can release a 1.0 version of `django-simple-deploy`. The 1.0 release will signify that this tool can be used reliably and predictably for all the anticipated use cases.

| Symbol | Status |
| :---: | :--- |
| :fontawesome-regular-square: | Not yet implemented |
| :fontawesome-regular-square-check: | Preliminary implementation |
| :fontawesome-solid-square-check: | Full implementation |

## Support the most popular Python package managers

| Platform | Bare `requirements.txt` file | Poetry | Pipenv |
| :------: | :--------------------------: | :----: | :----: |
| Fly.io   | :fontawesome-solid-square-check: | :fontawesome-solid-square-check: | :fontawesome-solid-square-check: |
| Platform.sh | :fontawesome-solid-square-check: | :fontawesome-regular-square-check: | :fontawesome-solid-square-check: |
| Heroku | :fontawesome-solid-square-check: | :fontawesome-solid-square-check: | :fontawesome-solid-square-check: |

!!! note
    When using Poetry on Platform.sh, we generate a `requirements.txt` file on the server. We should be able to strictly use Poetry instead.

## Support each major operating system

| Platform | Windows | macOS | Linux (Debian flavors) |
| :------: | :--------------------------: | :----: | :----: |
| Fly.io   | :fontawesome-solid-square-check: | :fontawesome-solid-square-check: | :fontawesome-regular-square-check: |
| Platform.sh | :fontawesome-solid-square-check: | :fontawesome-solid-square-check: | :fontawesome-regular-square-check: |
| Heroku | :fontawesome-solid-square-check: | :fontawesome-solid-square-check: | :fontawesome-regular-square-check: |

!!! note
    - I've done almost all of my development work on macOS, so initially that's the best-supported platform.

## Friendly summary of deployment process

All runs of `simple_deploy` produce a log file, which is helpful for troubleshooting. But we also aim to produce a friendly summary of the deployment process that briefly describes what was done, how to redeploy the project after making more changes locally, and how to start understanding the target platform's documentation.

| Fly.io | Platform.sh | Heroku |
| :--------------------------: | :----: | :----: |
| :fontawesome-regular-square: | :fontawesome-regular-square: | :fontawesome-regular-square-check: |

!!! note
    A very preliminary level of support was built for Heroku, as a proof-of-concept. This is not a difficult task, and it will be enjoyable to fill out this table.

    `simple_deploy` aims to make the initial deployment process friendlier and less error-prone, but our goal is also to help people become comfortable with their chosen platform. This friendly summary just provides some helpful jumping-off points, so people don't have to approach their platform's documentation completely on their own. We're basically pointing users to the parts of a platform's documentation that have been most relevant and helpful in understanding Python deployments on that platform.

## Support nested and non-nested Django projects

When you run `startproject` you can choose whether to run it with or without a trailing dot. The trailing dot, ie `django-admin startproject blog .` tells Django to place `manage.py` in the root directory of the project. This is a "non-nested project", because `manage.py` is not nested within the project. if you leave out the dot, `manage.py` is placed in an inner directory, creating a nested project structure.

This matters to platforms because some platforms look for `manage.py` in the root project folder.

| Project Structure | Fly.io | Platform.sh | Heroku |
| :------: | :--------------------------: | :----: | :----: |
| non-nested projects | :fontawesome-solid-square-check: | :fontawesome-solid-square-check: | :fontawesome-solid-square-check: |
| nested projects | :fontawesome-regular-square: | :fontawesome-regular-square: | :fontawesome-regular-square: |

!!! note
    Some work has been done to attempt support on Heroku, but that's probably the most difficult platform to support. This table will fill in more quickly when there's time to look at projects that use a Dockerfile, where we can move files around during every deployment push without affecting the local project.

## Overall stability of deployment process

Support for a new platform starts out as a proof-of-concept, showing that deployment to that platform can be automated. Full stability means people can use `simple_deploy` on a variety of projects with predictable, stable results. It also means the deployment is configured using best practices for that platform. For example, if it's a container-based platform, we produce a Dockerfile that you can build on as your deployment grows.

| Fly.io | Platform.sh | Heroku |
| :--------------------------: | :----: | :----: |
| :fontawesome-solid-square-check: | :fontawesome-solid-square-check: | :fontawesome-solid-square-check: |

## Other notes

There are a number of other questions to answer formally, and tasks to complete, before releasing a 1.0 version:

- [ ] Is the API stable enough for a 1.0 release?
- [ ] Should we adopt a plugin-based approach?
    - [ ] If not, what's the plan when a number of additional platforms want to build support into `django-simple-deploy`?
    - [ ] One of the goals of this project is to insulate the community from a platform that lets its docs and support tools go stale. If we have a plugin model, how do we keep the deployment process up to date when a platform isn't maintaining its plugin? Is there a submodule-based approach where the plugins can live here, and staff from platforms can have commit access to their submodule?
    - [ ] Should this be an org, and each plugin is in a repo on the org? Does that give us commit access to all plugins?
- [ ] Write a deprecation plan for platforms that go out of business, or are no longer appropriate for `simple_deploy` to support.
- [ ] Write a stability policy.
- [ ] Review all open issues, and label everything as pre-1.0 and post-1.0. Complete all pre-1.0 tasks.
