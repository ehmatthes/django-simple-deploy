django-simple-deploy
===

This app gives you a management command that configures your project for an initial deployment. It targets Heroku at the moment, but could be expanded to target other platforms as well.

Quick start
---

If you haven't already done so, install the Heroku CLI and make sure you're using Git to track your project. Then you can deploy your project using these steps:

- Install the package `django-simple-deploy`.
- Add `simple_deploy` to `INSTALLED_APPS`.
- Run `heroku create`.
- Run `python manage.py simple_deploy`.
- Commit the new files and changes that `simple_deploy` makes.
- Run `git push heroku main`.
- Run `heroku run python manage.py migrate`.

That's it; your project should now be deployed and running on Heroku.