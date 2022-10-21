---
title: Merging PRs
hide:
    - footer
---

Merging PRs
---

- Contributors should make all their changes on a development branch. They are free to make as many in-progress commits as they need, but should aim for a final atomic PR.
- Contributors should create a PR on GitHub.
- When appropriate, a maintainer will merge the PR, using squash & merge through the GitHub interface.
    - Write a one-line commit message summarizing the PR, appropriate for one-line `git log` output.
    - For more significant PRs, write a longer message summarizing the major points of what was done.
- Everyone pulls changes to their local `main` branch: `git pull origin main`