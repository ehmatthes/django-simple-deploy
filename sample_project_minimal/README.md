Minimal Sample Project
===

This is a minimal Django project; it is the result of running `django-admin startproject mysite .` It is meant for testing aspects of `django-simple-deploy` that do not need a fully functioning project, such as dependencies beyond Django. For example, this is the project used to test invalid CLI calls, because the result of those calls should not depend on the complexity of the target project at all.

This is kept separate from the main sample blog project because this project will likely receive less attention. For example, people should not be trying to use this project for their first use of `simple_deploy`.