Full list of CLI arguments
===

There are a number of flags you can use to customize the deployment process. Briefly, these flags allow you to choose which platform to target, make necessary platform-specific choices, control the degree of automation in the deployment process, and disable logging.

Table of Contents
---

- [All arguments](#all-arguments)
- [Specifying a platform](#specifying-a-platform)
    - [`--platform heroku`](#platform-heroku)
    - [`--platform platform_sh`](#platform-platform-sh)
        - [`--deployed-project-name`](#deployed-project-name) 
        - [`--region`](#region)
- [Other arguments](#other-arguments)
    - [`--automate-all`](#automate-all)
    - [`--no-logging`](#no-logging)
    - [`--ignore-unclean-git`](#ignore-unclean-git)


All arguments
---

The full list of arguments is shown here, with the default value listed first for each argument. If no options are listed, the argument is a simple boolean flag:

```
$ python manage.py simple_deploy
    --platform [heroku|platform_sh]              # required
        # Optional for Platform.sh deployments
        --deployed-project-name [project_name]   # default: name used in `startproject` command
        --region [region_name]                   # default: us-3.platform.sh
    --automate-all
    --no-logging
    --ignore-unclean-git
    
```

Specifying a platform
---

Right now, you can choose between two platforms: Heroku and Platform.sh.

### `--platform heroku`

This command will configure the project for deployment to Heroku, but you will need to commit changes and push the project:

```
$ python manage.py simple_deploy --platform heroku
```

There are no other arguments specific to Heroku deployments.

--

### `--platform platform_sh`

This command will configure your project for deployment to Platform.sh; again, you'll have to commit changes and push the project:

```
$ python manage.py simple_deploy --platform platform_sh
```

There are two optional arguments that are specific to Platform.sh deployments.

#### `--deployed-project-name`

Normally, `simple_deploy` identifies the name of the project through inspection. If you've already created an empty project on the target platform, we run a command such as `platform project:info` to discover the name that was used when creating the project. If you're using `--automate-all`, simple_deploy will determine the name used when running `startproject`, and use this name as the deployed project name.

However, there are situations where you may want to provide a specific name to use for the deployed project. This may be helpful, for example, when working with a GitHub-based approach to deployment where simple_deploy is just taking care of configuration.

The `--deployed-project-name` flag allows you to specify exactly what name to use for the deployed project. Note that if you provide this name and it differs from what was used to create the deployed project, the configuration will likely not work.

Example usage:

```
$ python manage.py simple_deploy --platform platform_sh --deployed-project-name my_blog_project
```

#### `--region`

The name of the region you want to create the project in. This usually refers to a datacenter location. The default is `us-3.platform.sh`, but you may want to choose a region closer to your location. You can see a list of all available locations by running `platform help project:create`.

Example usage:

```
$ python manage.py simple_deploy --platform platform_sh --region us-2.platform.sh
```


Other arguments
---

#### `--automate-all`

By default, `simple_deploy` configures your project for deployment but leaves you to actually push the project. If you want to have simple_deploy do everything for you, include the `--automate-all` flag:

```
# Automated Heroku deployment:
$ python manage.py simple_deploy --platform heroku --automate-all

# Automated Platform.sh deployment:
$ python manage.py simple_deploy --platform platform_sh --automate-all
```

For more information about what `--automate-all` does for you, see the section "Configuration-only use" on the [Heroku documentation](heroku_deployments.md) page.

#### `--no-logging`

By default, `simple_deploy` generates a log file that's stored in a `simple_deploy_logs/` folder in your project's root directory. Most webapp logs are stored in a lower-level system directory, outside the actual project folder. That's because the entire server is usually dedicated to serving the project. In this case, `simple_deploy` is adding a log folder to your local version of the project. This log currently contains a copy of most of the output that's shown on the terminal when you run `simple_deploy`. When you close the terminal where you ran `simple_deploy`, you will still have a record of the details of your deployment. This should be quite helpful to some users, and is critical in troubleshooting deployments. The log directory is added to `.gitignore`, so it won't be pushed to the deployment server. You are free to delete this folder at any point.

If you want to disable logging, you can do so with the `--no-logging` flag.

Example usage:

```
$ python manage.py simple_deploy --platform platform_name --no-logging
```

#### `--ignore-unclean-git`

We really want users to have a clean `git status` before running simple_deploy. This allows people to easily revert configuration changes if deployment doesn't work, or if they want to target a different platform. The `--ignore-unclean-git` flag allows users to override this recommendation.

Example usage:

```
$ python manage.py simple_deploy --platform platform_name --ignore-unclean-git
```