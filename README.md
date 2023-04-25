# django-simple-deploy

Initial Django deployments made easy.

## Documentation

The full documentation for this project is at [Read the Docs](https://django-simple-deploy.readthedocs.io/en/latest/).

Some documentation has not been moved to Read the Docs yet. You may find what you're looking for in the `old_docs/` directory, but some of that information is out of date.

## Quickstart

This app gives you a management command that configures your project for an initial deployment. It targets [Fly.io](https://fly.io), [Platform.sh](https://platform.sh), and [Heroku](https://heroku.com) at the moment, and can be expanded to target other platforms as well.

If you have a relatively simple Django project that runs locally, you can deploy your project in a few short steps. The only change you'll need to make to your project is to add this app to `INSTALLED_APPS`.

![Simplest example of how to use django-simple-deploy](https://raw.githubusercontent.com/ehmatthes/django-simple-deploy/main/assets/simplest_example.png)

The above command will deploy your project to Heroku. To deploy to another platform such as Platform.sh, just change the `--platform` argument:

```sh
python manage.py simple_deploy --platform platform_sh
```

All output is captured and written to a log file stored in `simple_deploy_logs/`, which is placed at the project's root directory.
