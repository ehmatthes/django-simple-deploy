---
title: Rationale
hide:
    - footer
---

# Rationale

`django-simple-deploy` solves a long-standing problem in the Django community: *How can we make people's initial deployment experience as straightforward as possible?*

This has not been an easy problem to address, because when it comes to deployment we find ourselves dependent on hosting platforms. These platforms may not have good documentation to begin with, they might have stale documentation and unmaintained support libraries, to name two common issues when dealing with hosting platforms.

> `django-simple-deploy` is a stable API for making initial deployments across multiple platforms.

`simple_deploy` is an abstraction layer between your project, and a hosting platform. As long as this project is maintained, you can configure your project for deployment by running `manage.py simple_deploy --platform platform_name`, against any supported platform. If the platform changes its deployment process, we just update this library and your deployment commands still work. This benefits people new to deployment, people familiar with deployment who just want to push simple projects, and people creating teaching resources that need more stability than a hosting platform can promise.

## Guiding questions

- How simple can the initial deployment process for a relatively simple (but nontrivial) Django project be?
- What platforms are most appropriate for automated configuration, and automated deployments?
- How much can we facilitate the learning process for Django developers, without doing a platform's work for them?
- How much can we influence platform providers in implementing a positive Django deployment story?

## Vision

Everyone who learns Django has a similar path. They pick some resource - the Django docs, a book, a video course, a mentor - and they learn to develop a simple project on their local system. They reach a point where their project works on their system, and they want to see it available to everyone. So they ask, "How do I deploy this project?" Then they see how much there is to learn just to get their app to appear online.

What if people new to Django didn't have to dig into a platform's documentation in order to deploy their project? What if people could just make an account on a platform, run a few commands, and see their project deployed? That's the vision of django-simple-deploy.

The management command `python manage.py simple_deploy --platform platform_name --automate-all` allows people to push their project to a cloud provider in four steps. There's still plenty to learn about deployment, but this project allows people to see their project deployed before they dig into their provider's documentation.
