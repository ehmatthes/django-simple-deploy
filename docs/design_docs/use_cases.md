---
title: Use Cases
hide:
    - footer
---

# Use cases

There are a number of use cases that are worth spelling out, because they can help guide the overall project. Understanding the full range of use cases can help make decisions about the overall API, which platforms to support, and more.

## People new to deployment

People who are new to deployment have to choose a platform, find the relevant documentation on that platform's site, modify their project, and push their project using that platform's CLI or deployment workflow. There are many obstacles to a successful first deployment, many of which are not the user's fault.

## People experienced with deployment

Even if you know how to deploy a Django project, a lot of the work to configure a simple project for deployment can be automated. `django-simple-deploy` should be helpful to people who fit this description as well.

## People experimenting with other platforms

When people outgrow their go-to deployment platform, they look around at other platforms. It is laborious to learn how to deploy a Django project on a number of different platforms, even if you are experienced with deployment in general. Even if you follow a platform's Django docs and push your project successfully, it doesn't mean you have an optimal Django configuration on that platform. A mature version of `django-simple-deploy` would give you a working deployment quickly, which you can then examine and compare to the platform's documentation, and configuration for other platforms as well.

## Authors/creators, teachers and trainers

Creating learning resources that cover deployment is notoriously difficult. One of the main reasons for this is stability, or the lack thereof. When you develop a tutorial for Django that includes deployment, you cross your fingers and hope the deployment process is stable during the life of your tutorial. Ultimately, you have no control over this. With a mature `django-simple-deploy`, any changes in the deployment process live behind the abstraction layer that `simple_deploy` offers. When a platform changes its recommended configuration, your instructions wouldn't change. Some of your instructions might change, especially related to maintaining the deployment, but the initial deployment would still work. This is a nice buffer between you as an author, and a constantly-evolving platform host.

This does not just apply to people teaching deployment. If you're focusing on a different aspect of Django development, but having a deployed version of the project would be nice, `simple_deploy` could be a helpful way to have your readers deploy their project, without having to spend a lot of time covering the deployment process.

## Platform hosts

Platform providers might benefit from a mature version of `django-simple-deploy` as well. Ever provider needs to include detailed documentation for how to deploy a Django project; there's no way around that. No one can develop a `simple_deploy` script for a new platform without some form of documentation for that platform. However, platform providers may want to include a short call-out at the top of a "Getting Started" writeup, showing how to get a working Django deployment on their platform quickly. Then readers could explore the working deployment, rather than having to get every deployment step right on their own the first time through the deployment process.

When new users can't get a project deployed successfully, they're likely to abandon the platform. `simple_deploy` could be a useful tool in onboarding for platform providers.
