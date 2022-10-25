---
title: Merging PRs
hide:
    - footer
---

Reviewing PRs
---



- Fetch the PR branch to your local repository: `git fetch origin pull/ID/head:BRANCH_NAME`
    - For more, see [Checking out pull requests locally](https://docs.github.com/en/pull-requests/collaborating-with-pull-requests/reviewing-changes-in-pull-requests/checking-out-pull-requests-locally).
- Check out the branch.
- Make review comments based on local review.

Merging PRs
---

- Contributors should make all their changes on a development branch. They are free to make as many in-progress commits as they need, but should aim for a final atomic PR.
- Contributors should create a PR on GitHub.
    - In the initial comment box when opening a PR, contributors should make any comments about the changes they've made that would help in code review.
- When appropriate, a maintainer will merge the PR, using `squash and merge` through the GitHub interface.
    - In the comment box for the `Confirm squash and merge` step, write a one-line commit message summarizing the PR, appropriate for one-line `git log` output.
    - For more significant PRs, write a longer message summarizing the major points of what was done. When you're finished writing the message, please delete the bullet points from the individual commits in the PR.
- Everyone pulls changes to their local `main` branch: `git pull origin main`