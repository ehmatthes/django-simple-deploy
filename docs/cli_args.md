Full list of CLI arguments
===

There are a number of flags you can use to customize the deployment process. Briefly, these flags allow you to choose which platform to target, make necessary platform-specific choices, control the degree of automation in the deployment process, and disable logging.

Table of Contents
---

- [All arguments](#all-arguments)
- [Platform arguments](#platform-arguments)
    - [Deployment to Heroku](#deployment-to-heroku)
- [Automation](#automation)
- [Logging](#logging)    


All arguments
---

The full list of arguments is shown here, with the default value listed first for each argument. If no options are listed, the argument is a simple boolean flag:

```
$ python manage.py simple_deploy
    --platform [heroku|platform_sh]    # required
    --automate-all
    --no-logging
```

Platform arguments
---

Right now, you can choose between two platforms: Heroku and Platform.sh.

### Deployment to Heroku

This command will configure the project for deployment to Heroku, but you will need to run some git commands:

```
$ python manage.py simple_deploy --platform heroku
```

This command will automate the entire process of pushing to Heroku, once you have installed django-simple-deploy and added simple_deploy to `INSTALLED_APPS`:

```
$ python manage.py simple_deploy --automate-all --platform heroku
```

### Deployment to Platform.sh

This command will configure your project for deployment to Platform.sh:

```
$ python manage.py simple_deploy --platform platform_sh
```

The `--automate-all` flag is not yet supported for Platform.sh.

Automation
---

By default, simple_deploy configures your project for deployment but leaves it to you to actually push the project. If you want to have simple_deploy do everything for you, include the `--automate-all` flag:

```
$ python manage.py simple_deploy --automate-all --platform heroku
```

For more information about what `--automate-all` does for you, see the section "Configuration-only use" on the [Heroku documentation](heroku_deployments.md) page.

Logging
---

By default, simple_deploy generates a log file that's stored in a `simple_deploy_logs/` folder in your project's root directory. Most webapp logs are stored in a lower-level system directory, outside the actual project folder. That's because the entire server is usually dedicated to serving the project. In this case, simple_deploy is adding a log folder to your local version of the project. This log currently contains a copy of all the output that's shown on the terminal when you run simple_deploy. When you close the terminal where you ran simple_deploy, you will still have a record of the details of your deployment. This should be quite helpful to some users, and is critical in troubleshooting deployments. The log directory is added to ``.gitignore``, so it won't be pushed to the deployment server. You are free to delete this folder at any point.

If you want to disable logging, you can do so with the `--no-logging` flag:

```
$ python manage.py simple_deploy --no-logging --platform platform_name
```
