Azure Deployments
===

This page discusses Azure deployments in more detail. Before reading this page, make sure you've read the relevant parts of the [main readme file](../README.md).

Table of Contents
---

- []()

Detailed description of Azure deployments
---

Automating deployment to Azure works a little differently than deploying to Heroku. Azure requires you to create some resources before pushing code to the server. Here's a breakdown of what django-simple-deploy does to push your project to Azure. You can see all of this in the file `simple_deploy/management/commands/utils/deploy_azure.py`.

### Requires --automate-all

When deploying to Azure, there are so many steps to do that only taking care of configuration doesn't help that much. Heroku encapsulates a lot of work in their `heroku create` command. Azure does not have a similar command; they require you to make a 'plan', then a 'resource group', and then a number of other steps before you can even configure your code and push your project to the server.

Because of all this, Azure deployments only work using the `--automate-all` flag. Anyone who doesn't want to use this flag should be ready to dig into the Azure documentation and deploy without using django-simple-deploy.

### Acknowledge the preliminary status of Azure deployments with django-simple-deploy

The django-simple-deploy project only has preliminary support for Azure deployments at this point. We really want to make this clear to users, so users must acknowledge this before running the deployment script.

### Adds the django-simple-deploy requirement

The app `simple_deploy` must be listed in `INSTALLED_APPS` before you can run the `simple_deploy` command. That means it's going to be listed in the settings file in the deployed version, which means the deployed version will need a copy of `simple_deploy`. So we make sure it's in the project's requirements.

### Configures the database

Azure deployments currently use a Postgres database. This database currently costs $0.034/hour, or $24.82/month. The script adds the appropriate lines to the settings file to connect to the Azure Postgres instance, and adds `psycopg2` to the project's requirements.

### Configures static files

The script adds `whitenoise` to the project's requirements, and modifies settings to use `whitenoise` in the deployed version of the project.

### Adds a migration script

The script adds a one-line shell script to the project, `run_azure_migration.sh`, which makes it possible to automatically run the initial migration after pushing the project to Azure.

### Adds the db-up Azure CLI extension

The db-up extension is required to interact with the Azure Postgres database.

### Creates an Azure resource group

Azure deployments require a resource group. The script makes a new resource group called `SimpleDeployGroup`.

### Creates an Azure App Service plan

Azure deployments require a plan. The script creates a plan called `SimpleDeployPlan` on the F1 (free) tier. This is the default behavior. You can use the `--azure-plan-sku` argument to specify a different plan, but this argument is primarily available for development purposes. The script uses the `--is-linux` flag to build a Linux server.

### Creates a unique app name

Azure deployments require a unique app name, in order to generate a unique URL for the project. The script generates an app name of the form `project-name-uniquestring`, where `uniquestring` is a 16-character alphanumeric string.

### Modifes `ALLOWED_HOSTS`

Now that an app name has been identified, we know the URL that will be used for the project. This URL is added to `ALLOWED_HOSTS` in the deployment section of settings.py.