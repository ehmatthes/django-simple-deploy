---
title: Introduction
hide:
    - footer
---

# django-simple-deploy

`django-simple-deploy` configures your Django project for deployment to a number of different platforms. For some platforms, it can automate the entire deployment process. Currently, three platforms have preliminary support: [Fly.io](https://fly.io), [Platform.sh](https://platform.sh), and [Heroku](https://heroku.com).

Here's what automated deployment on [Fly.io](https://fly.io) looks like:

```sh
$ pip install django-simple-deploy
# Add simple_deploy to INSTALLED_APPS.
$ python manage.py simple_deploy --platform fly_io --automate-all
```

After these three steps, your project should open in a new browser tab. :)

## Quick Start

For help deploying to a specific platform, start here:

- [Deploying to Fly.io](quick_starts/quick_start_flyio.md)
- [Deploying to Platform.sh](quick_starts/quick_start_platformsh.md)
- [Deploying to Heroku](quick_starts/quick_start_heroku.md)

## More resources

- If you're not sure which platform to choose, here's an [overview](general_documentation/choosing_platform.md) of the different platforms.
- If you're interested in the motivations for `django-simple-deploy`, start with the [Rationale](design_docs/rationale.md).
- If you're interested in helping out, see the [Contributing](contributing/index.md) page.

Note: The original documentation for this project was in the [GitHub repo](https://github.com/ehmatthes/django-simple-deploy/tree/main/old_docs), and some parts of the documentation have not been moved here yet.
