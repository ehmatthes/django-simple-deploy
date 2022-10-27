---
title: "Testing on Your Own Account"
hide:
    - footer
---

# Testing on Your Own Account

There's really no way around the requirement to be comfortable deploying projects to a personal account if you want to contribute to `django-simple-deploy`. You can run unit tests without making any network calls, but it's hard to fully understand this project without making some actual deployments to at least one of the supported platforms. While we may end up with some support for running CI tests on GitHub, there is no way to offer contributors individual support for running test deployments during their own development work.

Most development work incurs very little cost; however this is highly dependent on your vigilance in making sure to destroy projects shortly after each deployment. For example the integration tests make actual deployments, and they prompt you to automate the destruction of all resources created in the test run. If you choose no, or if anything interrupts the completion of the test run, you can be left with active projects on the platform you're working with.

## Choosing a Platform

If you're concerned about costs, you can look for platforms that have extended free trials. The [Choosing a Platform](../general_documentation/choosing_platform.md) page may help you find a platform that's suitable for testing with a low risk of incurring charges.