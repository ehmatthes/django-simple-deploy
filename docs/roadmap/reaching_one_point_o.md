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
| Fly.io   | :fontawesome-regular-square: | :fontawesome-solid-square-check: | :fontawesome-regular-square: |
| Platform.sh | :fontawesome-regular-square: | :fontawesome-solid-square-check: | :fontawesome-regular-square: |
| Heroku | :fontawesome-regular-square-check: | :fontawesome-solid-square-check: | :fontawesome-regular-square-check: |

!!! note
    - I've done almost all of my development work on macOS, so initially that's the best-supported platform.
    - I first built the project around Heroku, so I initially tested it on all three OSes. I haven't tried it for a long time, so I'm not sure where the support is on Windows and Linux at the moment.
    - This is the next focus for my work, so this table should be filled in before long.

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
| :fontawesome-regular-square-check: | :fontawesome-regular-square-check: | :fontawesome-regular-square-check: |

!!! note
    - On Fly.io, we create a database and connect it to the app that the user created, or that we created in a fully automated run. But if they were to run `simple_deploy` multiple times, they'd create a new database each time. That could get costly quickly, so we bail if we detect a database on the user's account. This means people can only use `simple_deploy` on Fly.io if they'd don't already have a project deployed there. This process needs to be refined.
    - Platform.sh is probably closest to having a stable process. The process needs a little more review, and needs some refinements such as setting a more specific value for `ALLOWED_HOSTS`. We also need to look at how well `simple_deploy` supports someone who's pushing multiple projects to Platform.sh.
    - Heroku recently dropped their free tier. This doesn't affect `simple_deploy` a whole lot, but the process needs some review around which resources are configured automatically for Heroku deployments, and how clearly we are communicating this to users.

## Other notes

There are a number of other questions to answer formally, and tasks to complete, before releasing a 1.0 version:

- [ ] Is the API stable enough for a 1.0 release?
- [ ] Should we adopt a plugin-based approach?
    - [ ] If not, what's the plan when a number of additional platforms want to build support into `django-simple-deploy`?
- [ ] Write a deprecation plan for platforms that go out of business, or are no longer appropriate for `simple_deploy` to support.
- [ ] Write a stability policy.    
- [ ] Review all open issues, and label everything as pre-1.0 and post-1.0. Complete all pre-1.0 tasks.
