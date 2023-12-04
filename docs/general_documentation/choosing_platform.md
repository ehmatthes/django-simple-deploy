---
title: Choosing a platform
hide:
    - footer
---

# Choosing a Platform

Choosing a platform for your first deployment might seem difficult, because there are many options to choose from these days. It's hard to say that any one platform is better than any other, because they all take different approaches to a complex problem - pushing your project to a remote server in a way that lets it run reliably, at a reasonable cost.

`django-simple-deploy` aims to make it easier to choose a platform by simplifying your first deployments to a new platform. You don't have to do a deep dive into each platform's documentation in order to get a deployment up and running. Typically, you can make an account with the platform you're interested in, install that platform's CLI, specify that platform with the `--platform` flag, and then push your project to that platform. You get a working deployment with very little effort, which makes further exploration of each platform much easier and much less frustrating.

This page summarizes the major strengths and potential drawbacks of each platform.

*Note: Best efforts are made to keep this page up to date. If you see something that is no longer accurate, please [open an issue](https://github.com/ehmatthes/django-simple-deploy/issues) and include a link to the updated information.*

## Quick comparison

|                       | Fly.io             | Platform.sh             | Heroku                                                      |
| --------------------- | ------------------ | ----------------------- | ----------------------------------------------------------- |
| Credit Cards required for trial | Yes                | No                      | Yes |
| Free trial length     | Unlimited time | 30 days | No free trial |
| Cheapest paid plan    | $1.94/mo              | $10/mo                  | [$10/mo](https://blog.heroku.com/new-low-cost-plans) ($5 Eco dyno + $5 Mini Postgres)                     |
| Company founded       | 2017               | 2012                    | 2007                                                        |

## Detailed notes

=== "Fly.io"

    **Known for**

    * Fly.io automatically deploys your project to physical servers spread around the world. The goal is that your app will be equally responsive to users around the world.

    **Strengths**

    * Fly.io does not require a credit card for its free trial, and the free trial does not have a time limit.
    * Even after you enter a credit card, the free offering is enough to keep a small app running.
    * Offers a [public forum](https://community.fly.io) for support, and allows you to search for issues (and resolutions) that others have had.
    * Fly.io seems to be well regarded in the post-Heroku era.

    **Issues**

    * I am not aware of any specific issues with Fly.io at the moment, but the distributed server model may not be suitable for all projects.

    **Links**

    * [Fly.io home page](https://fly.io/)
    * [Pricing](https://fly.io/docs/about/pricing/)
    * [Docs home page](https://fly.io/docs/)
    * [CLI installation](https://fly.io/docs/hands-on/install-flyctl/)
    * [CLI reference](https://fly.io/docs/flyctl/)

    **Using `django-simple-deploy` with Fly.io**

    - [Quick start: Deploying to Fly.io](../quick_starts/quick_start_flyio.md)

=== "Platform.sh"

    **Known for**

    * Platform.sh is a managed hosting platform that focuses on making continuous deployment easy and safe. They even tell you it's okay to deploy on Fridays. :)

    **Strengths**

    * Platform.sh does not require a credit card for its free trial.
    * Once you have an environment set up with the Platform.sh tools, pushing a project and maintaining it is as straightforward as it is on any other comparable platform.


    **Issues**

    * Error messages about resource usage are unclear. For example, new users are limited to two new apps per day until they have been billed successfully three times. Since billing occurs once a month, this limit applies for several months, even though you're willing to pay for usage. Also, if you try to create a new project and it fails because of this issue, you don't get a specific error message. You have to contact support to find out if this is the reason for failure, or if something else went wrong.
    * The CLI requires PHP for installation, and requires a bash shell for deployment. This isn't particularly difficult on macOS or Linux, but installation is not straightforward on Windows if you don't already have Windows Subsystem for Linux (WSL) installed, or a comparable bash-compatible environment.

    **Links**

    * [Platform.sh home page](https://platform.sh)
    * [Pricing](https://platform.sh/pricing/)
    * [Docs home page](https://docs.platform.sh)
    * [CLI installation](https://docs.platform.sh/administration/cli.html)

    **Using `django-simple-deploy` with Platform.sh**

    - [Quick start: Deploying to Platform.sh](../quick_starts/quick_start_platformsh.md)

=== "Heroku"

    **Known for**

    * Heroku was the original "Platform as a Service:" (PaaS) provider. Heroku pioneered the simple `git push heroku main` deployment process that most other platforms are trying to build on today.
    * Heroku is known for being more expensive than options such as VPS providers, and AWS. However, they quite reasonably argue that using Heroku requires less developer focus than unmanaged solutions like a VPS or AWS. You get to spend more of your time building your project, and less time acting as a sysadmin.

    **Strengths**

    * Heroku has been managing automated deployments longer than any of the other platforms supported by `django-simple-deploy`.

    **Issues**

    * Heroku was a great platform in the late 2000s through the mid 2010s, but then it began to stagnate. Packages that were recommended for deployment were archived and unmaintained, even though they were officially still recommended. Heroku "just worked" for a long time, but recently that neglect has caught up to them. They are in the midst of restructuring their platform, and people are reasonably concerned about Heroku's long-term stability.
    * Heroku has had major incidents and outages in recent years, which they took a long time to resolve and communicated poorly about. This is the more significant reason many people have moved away from them in recent years.
    * Heroku was famous for a very generous free tier, where you could deploy up to 5 apps at a time including a small Heroku Postgres database. This kind of offering sounds nice, but it also draws abuse. Heroku was constantly fighting things like auto-deployed crypto miners. They no longer offer a free tier. Their cheapest plans are still reasonably priced, though, so the end of the free tier should not rule them out as a hosting option.

    **Links**

    * [Heroku home page](https://www.heroku.com)
    * [Pricing](https://www.heroku.com/pricing)
        * *Note: Heroku's lowest-priced tiers were recently [restructured](https://blog.heroku.com/new-low-cost-plans).*
    * [Docs home page](https://devcenter.heroku.com)
    * [CLI installation](https://devcenter.heroku.com/articles/heroku-cli)
    * [CLI reference](https://devcenter.heroku.com/categories/command-line)
    * [Python on Heroku](https://devcenter.heroku.com/categories/python-support)
    * [Getting Started on Heroku with Python](https://devcenter.heroku.com/articles/getting-started-with-python?singlepage=true)
    * [Deploying Python and Django Apps on Heroku](https://devcenter.heroku.com/articles/deploying-python)

    **Using `django-simple-deploy` with Heroku**

    - [Quick start: Deploying to Heroku](../quick_starts/quick_start_heroku.md)

---
