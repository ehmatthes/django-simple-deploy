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

## Destroying Resources

Keep in mind that some platforms create more than one resource per deployment. For example on Fly.io, each deployment creates a new project, and a corresponding database. Destroying the project does not destroy the database. It is your responsibility to identify what resources were created on each test run, and to verify that all of these resources were actually destroyed.

## Higher-Tier Resources

The default configuration for all platforms uses the cheapest resources that result in a reasonably working deployment on that platform. Usually this is the cheapest (hopefully free) resource available. Sometimes, however, we know that using the cheapest resource will result in a deployment that's so slow it's effectively useless. In this case we use the lowest-tier resource that is likely to provide a minimally functional working deployment.

When testing, especially with repeated pushes, using the cheapest resources can cause problems. When making repeated deployments using the cheapest resources, your account can end up hitting some fraud and abuse limits that are not communicated explicitly. This is reasonable on the part of platforms; if they give explicit messages in these situations, people will focus their abuse efforts in a way that makes it harder for the platform to stay in business.

To test `django-simple-deploy` effectively, you may see suggestions to bump the configuration to higher-tiered resources that cost more than you'd want to pay if you kept the deployment active. A $100/month resource that's billed by the minute can be quite reasonable to test against, because $100/month works out to $0.002/minute. So a project that's created and destroyed in less than ten minutes should cost about $0.02. But, if you mess up and forget to verify the project was actually destroyed, you can end up incurring significant charges. You are entirely responsible for these charges, and we can not reach out to platforms on your behalf in these situations.
