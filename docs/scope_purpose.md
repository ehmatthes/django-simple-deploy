Scope and Purpose
===

If you're interested in helping to develop this project, or in evaluating its appropriateness for a specific purpose, it's helpful to know the intentions behind the project and its vision for the future. The core purpose is to help people new to Django make their first deployments as easily as possible. The rest of this page clarifies exactly what that means.

Table of Contents
---

- [Vision](#vision)
- [Audience](#audience)
    - [Who this project is for](#who-this-project-is-for)
    - [Who this project is not for](#who-this-project-is-not-for)
- [Project goals](#project-goals)
    - [What this project will do](#what-this-project-will-do)
    - [What this project will not do](#what-this-project-will-not-do)
- [Feedback](#feedback)

Vision
---

Everyone who learns Django has a similar path. You pick some resource - the Django docs, a book, a video course, a mentor - and you learn to develop a simple project on your local system. You reach a point where your project works on your system, and you want to see it available to everyone. So you ask, "How do I deploy this project?" Then you see how much there is to learn just to get your app to appear online.

What if people new to Django didn't have to dig into a platform's documentation in order to deploy their project? What if people could just make an account on a platform, run a few commands, and see their project deployed? That's the vision of django-simple-deploy.

The management command `python manage.py simple_deploy --automate-all` allows you to push your project to a cloud provider in three steps, as shown in the [main readme](../README.md). There's still plenty to learn about deployment, but this project allows people to see their project deployed before they dig into their provider's documentation.

Audience
---

### Who this project is for

It's tempting to think that a project like this is just for beginners. But that's a pretty limiting view. Here are all the users who might appreciate a well-implemented project like this:

- People who are new to programming, Python, and Django, and just want to see their project deployed to a live server as quickly and easily as possible.
- People who know how to do deployments, but have a simple project to share with someone and want a deployment done as quickly and easily as possible.
- Teachers and authors who are discussing something to do with webapps, where deployment is not the main focus.
    - For example, imagine someone who's writing a post about testing web apps and they want to discuss the differences between testing a local app and testing a deployed app. They don't have to walk people through deployment, they can just have students use `simple_deploy`.
    - One problem for authors is that cloud providers can change their process without any notice. If this project develops a stable API, these changes are hidden from users. Users still run `python manage.py simple_deploy --automate-all --platform awesome-cloud-provider`, even as providers change their deployment processes.
- People who want to easily compare different cloud providers.
    - The documentation for different cloud providers varies widely in terms of scope, usability, quality of maintenance, and more. For example the Heroku docs have been excellent, but they get out of date at times. Platform.sh has excellent documentation, but it can take a while to understand where to look when trying to complete your first deployment on that platform.
    - You can use `simple_deploy` to try a deployment on each of the platforms it supports, quickly and easily. Then you can poke around different versions of your project and see how each is configured for deployment, and how easily you can carry out subsequent deployments on those platforms.
- Platform providers who want to give users the simplest way possible to get a demo project deployed.
  - This project will need some maturity before it can be used in this way, but it's a good thing to think about ahead of time. This approach allows potential new users to have a deployed project up and running that they can then examine, rather than having to wade through documentation first and then see their project deployed.

### Who this project is not for

- Someone running a business.
    - This project will never be meant to support mission-critical projects.
- Projects that deal with payments.
    - If you're accepting payments, you should be understanding deployment at a deep enough level to not need a project like this. Or, you should pay someone who understands deployment well enough to not need this project.
- Overly complex projects.
    - The `django-simple-deploy` project is tested against a basic Django project, and it will be developed to support as many Django features and use-cases as possible. But if your project has a degree of complexity that makes initial deployments using `simple_deploy` fail, you should probably be digging into your provider's documentation.        

Project goals
---

### What this project will do

This project will continue to evolve in the following directions:
- Support a small number of platforms, focusing on providers that:
    - Offer free or low-cost trial deployments.
    - Offer a CLI or API that makes it straightforward to automate the deployment process.
- Make reasonable decisions on behalf of end-users about which deployment options to use:
    - One of the challenges of reading providers' documentation is all of the different choices you have to make during the deployment process. The `simple_deploy` process uses the cheapest resources possible that are appropriate for initial deployments.
    - Note: These resources are not always free, and it is entirely the users' responsibility to understand and monitor any charges they may be accruing through use of this project.
- Generate project-specific documentation to help users understand their initial deployment:
    - Right now the project just generates output as it runs.
    - The project will likely generate a number of files that record what was done, and offer suggestions for how to carry out subsequent deployments. It should also include a number of links to specific parts of the provider's documentation, to help users better understand the platform they've chosen.

### What this project will not do

It's just as important to state what this project does not intend to do:
- This project will not support every cloud provider that supports Django:
    - This would be a daunting goal to keep up with.
    - The main goal is to help people understand and make an initial deployment, from a small number of providers that support automated deployment processes.
    - We are serving end users, not providers. Providers will benefit from a mature project like this, but they are not the core audience for the project.
- This project will not support overly complex deployments:
    - There are a number of more complex third-party packages that do aim to facilitate the development and deployment of complex Django projects. This is not one of those projects, and has no intention of becoming one.
    - The main red flag about which features to not support are features involving payments, and external service providers. For example, the project does not aim to support complex authentication services or workflows.

Feedback
---

This project is young, so if you have any feedback about what you read here please feel free to [open an issue](https://github.com/ehmatthes/django-simple-deploy/issues).