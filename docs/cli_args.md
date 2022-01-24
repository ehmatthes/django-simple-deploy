Full list of CLI arguments
===

There are a number of flags you can use to customize the deployment process. Briefly, these flags allow you to choose which platform to target, make necessary platform-specific choices, control the degree of automation in the deployment process, and disable logging.

Table of Contents
---

- [All arguments](#all-arguments)
- [Platform arguments](#platform-arguments)
    - [Deployment to Heroku](#deployment-to-heroku)
    - [Deployment to Azure](#deployment-to-azure)
- [Automation](#automation)
- [Logging](#logging)    


All arguments
---

The full list of arguments is shown here, with the default value listed first for each argument. If no options are listed, the argument is a simple boolean flag:

```
$ python manage.py simple_deploy
    --platform [heroku|azure]
    --azure-plan-sku [F1|B1|S1|P1V2|P2V2]
    --automate-all
    --no-logging
```

Platform arguments
---

Right now, you can choose between two platforms: Heroku and Azure. Currently, development is focused on refining Heroku deployments; deployment to Azure is experimental.

### Deployment to Heroku

These two commands are identical. They will configure the project for deployment to Heroku, but you will need to run some git commands:

```
$ python manage.py simple_deploy
$ python manage.py simple_deploy --platform heroku
```

These two commands are identical; they will automate the entire process of pushing to Heroku, once you have installed django-simple-deploy and added simple_deploy to `INSTALLED_APPS`:

```
$ python manage.py simple_deploy --automate-all
$ python manage.py simple_deploy --platform heroku --automate-all
```

### Deployment to Azure

Deployment to Azure is experimental. To deploy to Azure, you will need to specify the platform, and use the `--automate-all` flag:

```
$ python manage.py simple_deploy --platform azure --automate-all
```

If you run this command without the `--automate-all` flag, it will exit with a message to include the flag, and a brief explanation for why the flag is necessary.

#### Azure plan arguments

Azure seems to significantly impede the deployment process on the free plan at times. It can be beneficial to use a paid plan if you're trying Azure deployments. All Azure deployments incur a charge, because there is no free database offering on Azure. If you're experimenting with this, please make sure you understand Azure's billing process.

The following command will deploy to the lowest level of the [Basic service plan](https://azure.microsoft.com/en-us/pricing/details/app-service/linux/):

```
$ python manage.py simple_deploy --platform azure --automate-all --azure-plan-sku B1
```

Automation
---

By default, simple_deploy configures your project for deployment but leaves it to you to actually push the project. If you want to have simple_deploy do everything for you, include the `--automate-all` flag:

```
$ python manage.py simple_deploy --automate-all
```

For more information about what `--automate-all` does for you, see the section "Configuration-only use" on the [Heroku documentation](heroku_deployments.md) page.

Logging
---

By default, simple_deploy generates a log file that's stored in a `simple_deploy_logs/` folder in your project's root directory. Most webapp logs are stored in a lower-level system directory, outside the actual project folder. That's because the entire server is usually dedicated to serving the project. In this case, simple_deploy is adding a log folder to your local version of the project. This log currently contains a copy of all the output that's shown on the terminal when you run simple_deploy. When you close the terminal where you ran simple_deploy, you will still have a record of the details of your deployment. This should be quite helpful to some users, and is critical in troubleshooting deployments. The log directory is added to ``.gitignore``, so it won't be pushed to the deployment server. You are free to delete this folder at any point.

If you want to disable logging, you can do so with the `--no-logging` flag:

```
$ python manage.py simple_deploy --no-logging
```
