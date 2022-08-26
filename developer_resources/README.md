Developer Resources
---

This is a collection of resources that are useful in developing and maintaining django-simple-deploy. For example, having a sample of the output of actual CLI command calls saves us from having to run those commands repeatedly when writing code that parses the output.

Most identifying information has been replaced by something similar to `redacted_username`. Some specific information has been left in, such as a project ID, a project has already been destroyed.

- [Output of `platform create`](platform_create_output.txt)
    - This output uses the project name `my_deployed_blog` to be clearly distinct from the name `blog`, originally used with the `startproject` command.
- [Output of `platform project:info`](platform_project_info_output.txt)
    - This is the output after the `platform create` call, captured in [platform_create_output.txt](platform_create_output.txt).
