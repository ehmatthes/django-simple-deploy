Sample Project
---

This is a simple blog project that can be used to test the django-simple-deploy project. People can also use this blog project to try out django-simple-deploy.

Notes about project requirements
---

This project is mainly used for testing, and the full testing script is run against deployements that use `requirements.txt`, Pipenv, and Poetry. As such, you'll find multiple requirements files in the sample project; you'd be very unlikely to find this mix of multiple approaches in a real-world project.

The testing process currently copies the entire sample project to a tmp directory, and then removes the unneeded requirements files for the current test. If you are working with the sample project manually, you will probably want to remove all of the requirements files except the one that supports the dependency management approach you want to use. For example if you want to manually try out the `requirements.txt`-based approach, delete the `Pipfile` and the `pyproject.toml` files.

Nested vs not-nested projects
---

The [polls tutorial](https://docs.djangoproject.com/en/4.1/intro/tutorial01/) tells people to begin a project using the command `django-admin startproject mysite`, without a dot at the end. Most other resources I've seen, such as the [Django Girls tutorial](https://tutorial.djangogirls.org/en/django_start_project/), include a dot at the end of the `startproject` command: `django-admin startproject mysite .`

The dot at the end creates the project in the current directory; you end up with a folder matching your project name, containing files such as settings.py, urls.py, etc. The manage.py file is also at the root level. Without the dot you end up with a folder matching your project name, and then another folder with the same name inside that one. The settings.py, urls.py, and similar files are contained inside the nested folder. In this structure, manage.py is inside the first project_name/ directory.

Here's the file structure after running `django-admin startproject .` and then `manage.py startapp blogs`:

```
.
├── b_env
├── blog
│   ├── __init__.py
│   ├── __pycache__
│   │   ├── __init__.cpython-310.pyc
│   │   └── settings.cpython-310.pyc
│   ├── asgi.py
│   ├── settings.py
│   ├── urls.py
│   └── wsgi.py
├── blogs
│   ├── __init__.py
│   ├── admin.py
│   ├── apps.py
│   ├── migrations
│   │   └── __init__.py
│   ├── models.py
│   ├── tests.py
│   └── views.py
└── manage.py
```

Here's the file structure after running `django-admin startproject` and cd'ing into the `blog/` directory, and then running `manage.py startapp blogs`:

```
.
├── b_env
└── blog
    ├── blog
    │   ├── __init__.py
    │   ├── asgi.py
    │   ├── settings.py
    │   ├── urls.py
    │   └── wsgi.py
    ├── blogs
    │   ├── __init__.py
    │   ├── admin.py
    │   ├── apps.py
    │   ├── migrations
    │   ├── models.py
    │   ├── tests.py
    │   └── views.py
    └── manage.py
```

To create a nested version of the project from the unnested version:

- Duplicate the project.
- Create a folder inside the project called `blog/`.
- Move all current files to the inner `blog/` directory except `requirements.txt`, `Pipfile`, `pyproject.toml`, and `test_deployed_app_functionality.py`.
- Run `tree -L 3` to verify that the directory structure matches the above diagram.