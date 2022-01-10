Sample Project
---

This is a simple blog project that can be used to test the django-simple-deploy project. People can also use this blog project to try out django-simple-deploy.

Notes about project requirements
---

This project is mainly used for testing, and the full testing script is run against deployements that use `requirements.txt`, Pipenv, and Poetry. As such, you'll find multiple requirements files in the sample project; you'd be very unlikely to find this mix of multiple approaches in a real-world project.

The testing process currently copies the entire sample project to a tmp directory, and then removes the unneeded requirements files for the current test. If you are working with the sample project manually, you will probably want to remove all of the requirements files except the one that supports the dependency management approach you want to use. For example if you want to manually try out the `requirements.txt`-based approach, delete the `Pipfile` and the `pyproject.toml` files.