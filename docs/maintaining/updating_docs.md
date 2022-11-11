---
title: Updating Documentation
hide:
    - footer
---

It's important to keep the documentation updated as the project evolves. Here are some brief notes about how to think about documentation for `simple_deploy`, and some how-tos for maintaining the project's documentation.

## Guiding principles

### Audiences

There are four main audiences for the documentation:

- **End users**: People who want to use `simple_deploy` to deploy a project, and don't care about the internals of the project.
- **Authors and creators**: People who want to use `simple_deploy` to teach others how to deploy and work with Django projects.
- **Developers**: People who want to help develop `simple_deploy`, and keep it up to date. These are people who are working on simple_deploy locally, and who submit PRs to the project.
- **Maintainers**: People who are managing the long-term development and stability of the project. These are people who can merge PRs and make new releases.

All documentation should target one or more of these specific groups.

### Documentation sections

**End-user** documentation should be clear and to the point.

- People use `simple_deploy` in order to simplify deployment. The documentation that's written for them should support this mindset.
- The main pages targeting this audience is the Introduction and Quick Start pages.

Documentation for **authors and creators** should include more detailed information and explanations, without focusing on the project's internals.

- These people need to know a little more about how `simple_deploy` can be used, so they can best determine how to write or speak about it, or otherwise integrate it into their work.
- The main pages focused on this group are in the General Documentation section.

Documentation for **developers** should focus on design principles and project internals.

- These people need to understand some of the internals of `simple_deploy`.
- The Contributing, Design Documentation, and Unit Tests sections are relevant to this group.

Documentation for **maintainers** should focus on project architecture,  and maintenance tasks.

- This group needs to understand how to evaluate potential contributions to the project.
- This group needs to know how to carry out maintenance tasks for the project.
- The main section for this group is under Maintaining.

## Documentation framework (MkDocs)

Documentation uses [Material for MkDocs](https://squidfunk.github.io/mkdocs-material/).

- All documentation lives in `docs/`.
- The documentation configuration file `mkdocs.yml` lives in the root folder.
- The main help page for maintaining an established Material project is [here](https://squidfunk.github.io/mkdocs-material/reference/).

### Updating documentation

- To update the documentation, modify any of the existing files in `docs/`. If you feel the need to create a new section in the docs, please bring this up in an issue or discussion first.

### Viewing the documentation locally

To view the documentation locally, run `mkdocs serve` in the root directory of the project, in an active virtual environment. Visit the project at `http://localhost:8000`. If that port is in use, you can run `mkdocs serve --dev-addr localhost:PORT_NUMBER`.

## Releasing documentation

Updated documentation is automatically pushed to RtD once it's on the main branch. Every merge that involves documentation gets pushed automatically.
