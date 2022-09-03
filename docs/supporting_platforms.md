General Approach to Supporting Platforms
===

As the project matures, it's becoming clearer how each platform is supported. When simple_deploy acts on a project, there is some general work that's done regardless of what platform is being targeted; then there is additional platform-specific work that needs to be done.

This doc describes how that division of work is implemented. The goal of this doc is to understand how support for current platforms is implemented, and to make it easier to build support for new platforms.

Table of Contents
---

- [Overall Architecture](#overall-architecture)
    - [*simple_deploy.py*](#simple_deploypy)
    - [*deploy_platform-name.py*](#deploy_platform-namepy)
- [Templates and Messages](#templates-and-messages)
    - [Template files](#template-files)
    - [Message files](#message-files)
- [Supporting a New Platform](#supporting-a-new-platform)

Overall Architecture
---

The main work for modifying a project is done by two scripts, *simple_deploy.py* and a platform-specific file called *deploy_platform-name.py*.

### *simple_deploy.py*

*simple_deploy.py* does all of the platform-agnostic work:

- Parse the command.
    - What platform are we targeting, are we skipping logging, are we testing, etc.
- Validate the command.
    - Are all required arguments present?
    - Is there a conflicting set of arguments?
    - If using `--automate-all`, confirm the actions that will be taken on the user's behalf.
- Inspect the local system.
    - Are we on Windows, macOS, Linux?
- Inspect the project generally.
    - Determine the project name, project root directory, locate *.git/* directory, define the path to *settings.py*.
    - Make sure the output of `git status` contains `working tree clean`. This can be overridden with the `--ignore-unclean-git` flag.
    - Determine the dependency management system (bare *requirements.txt*, Pipenv, Poetry), and identify existing dependencies.
- Validate the project.
    - Exit if anything about the project indicates an inability to configure for deployment.
- Instantiate the platform-specific deployer, called `PlatformnameDeployer`.
    - Get any platform-specific confirmations, ie if a platform is in a preliminary state of support.
    - Inspect the project in the context of the target platform.
    - Check that all identifiable prerequisites are satisfied. For example if not using `--automate-all`, has an empty project been created on the platform? Most configuration-only deployments require this.
- Define helper methods that will be used by all platform-specific scripts, such as functions to make OS-specific CLI calls, write output to console and log files, and add requirements to the project.
- Call platform-specific `prep_automate_all()` method.
    - This is one of the steps most likely to fail, so call it first. If this fails, we don't want to take any other steps aside from setting up logging.
- Make platform-agnostic configuration changes to the project.
    - Build a log dir, if needed; make sure Git is ignoring log dir.
    - Add simple_deploy to dependencies.
- Call the `deploy()` method of the platform-specific deployer object.

### *deploy_platform-name.py*
    
A platform-specific file called *deploy_platform-name.py* does all of the platform-specific configuration. This is a class called `PlatformnameDeployer`, which is instantiated in *simple_deploy.py*. After completing all of its work, *simple_deploy* calls the `PlatformnameDeployer.deploy()` method, which does the following:

- Make any needed changes to settings.
    - All changes should be done in a way that only affects the project when run in the platform's environment.
- Add any platform-specific configuration files.
    - ie Heroku's *Procfile*, Platform.sh' *.platform.app.yaml*.
- Add any platform-specific requirements.
    - ie `gunicorn`, `psycopg2`
- Show a success message when finished.
    - Summarize changes that were made.
    - State the deployed project URL.
    - State next steps for deployment.
    - Point to logs, and friendly deployment summary.
- If using `--automate-all`:
    - Create new project, if it hasn't been made.
    - Add all changes and new files, and make commit.
    - Push changes.
    - Open project.

These changes are done in an order where failing at any point will have the least impact on the current state of the project.

Templates and Messages
---

### Template files

Template files can be used to generate whole files, such as Heroku's *Procfile* or Platform.sh' *.platform.app.yaml*. they can also be used to add blocks to existing files, such as adding a platform-specific settings block to the end of *settings.py*.

Template files are stored in *simple_deploy/templates/*.

### Message files

There are two kinds of messages used. Static messages are the same in all situations; dynamic messages have context-specific information embedded in them. For example if the user omits the `--platform` argument, they see a default static message. When a deployment is successful, the concluding success message includes the URL of the deployed project.

Platform-agnostic messages are stored in *simple_deploy/management/commands/utils/deploy_messages.py*. Platform-specific messages are stored in *simple_deploy/management/commands/utils/deploy_messages_platform-name.py*. 

Supporting a New Platform
---

*Please* get in touch before starting anything other than exploratory work in an attempt to support a new platform! This project is in active development, and there may be upcoming, unannounced changes that would invalidate some of your work on a new deployment script.

If you are developing support for a new platform:

- You shouldn't have to touch *simple_deploy.py*, except to add an `elif` block to `_check_platform()`.
- Clearly define the prerequisites for a configuration-only deployment. For example, make sure to require that users create an empty project on the target platform before running simple_deploy.
- Build a new *deploy_platform-name.py* file, modeled after one of the existing platform-specific deployer files. 
    - Make sure to structure this file so that configuration steps are made in the order of least impact on the local project. If we fail, we want to fail with minimal impact.