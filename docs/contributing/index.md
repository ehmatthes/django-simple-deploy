---
title: Contributing
hide:
    - footer
---

Thank you for your interest in helping out with `django-simple-deploy`! I hope that this project will be maintained as long as Django exists as a framework, so we really can use everyone's help.

There are many ways to contribute, and many reasons for contributing. This page is structured as a way to steer everyone into the most appropriate parts of the Contributing docs for their current situation.

Because `django-simple-deploy` touches on so many different things, there really is no one person who could be an expert on everything involved in the project. For example, no one is going to be an expert on the specific aspects of every platform that `django-simple-deploy` supports. That's especially true when you consider that employees of some of these platforms have already contributed to the project. If you're interested in helping out, there's almost certainly a place for you here.

Minimum Qualifications (Beginners Welcome!)
---

Because this project focuses on deployment of working Django projects, and has a few base requirements, there are some minimum qualifications for contributing to the project. You can start contributing if you:

- Know how to run a Django project on your local system.
- Know how to make commits and check the current status of a project using Git.
- Know how to use one of Python's dependency management systems, such as pip with a bare `requirements.txt` file, Poetry, or Pipenv.
- Have an active account on one of the platforms supported by `django-simple-deploy`, that you can push projects to.

It's helpful to have some familiarity with GitHub as well, but that's easy to learn if you meet the above requirements. If you meet these criteria, you can get involved in this project.

Ways to contribute
---

There are many ways to contribute. Choose the option that fits you best, and start contributing. :)

- If you have a long-term interest in contributing, please introduce yourself on the [Introductions](https://github.com/ehmatthes/django-simple-deploy/discussions/130) thread.
- If you're newer to Django, or new to deployment, the simplest way to help is by [documenting a test run](test_run.md).
- If you know a particular platform well, please share any thoughts you have about how to improve support for that platform:
    - You can make a [test run](test_run.md) on that platform and look at the configuration changes that `simple_deploy` makes for that platform.
    - Or, you can look in the `simple_deploy/management/commands/utils/` directory and find the `deploy_platform-name.py` file that targets the platform you know, and review the implementation details for configuration and deployment to that platform.
- Respond to either of the two open discussions:
    - [Open questions](https://github.com/ehmatthes/django-simple-deploy/discussions/132), a short list of questions related to reaching the stability needed for a 1.0 release.
    - [Working towards idempotency](https://github.com/ehmatthes/django-simple-deploy/discussions/169), a focused question about making sure repeated `manage.py simple_deploy` calls will not cause issues in a project.
- If you're ready to dig into the codebase, see the [Setting Up a Development Environment](development_environment.md) page.

Code of Conduct
---

`django-simple-deploy` operates under a clear [Code of Conduct](https://github.com/ehmatthes/django-simple-deploy/blob/main/old_docs/code_of_conduct.md).
