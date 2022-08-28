Developer Resources
---

This is a collection of resources that are useful in developing and maintaining django-simple-deploy. For example, having a sample of the output of actual CLI command calls saves us from having to run those commands repeatedly when writing code that parses the output.

Most identifying information has been replaced by something similar to `redacted_username`. Some specific information has been left in, such as a project ID, a project has already been destroyed. Also, if we're parsing for identifying information and it's helpful to have a string similar to what we've really found, actual information has been replaced by random strings with a similar structure.

- [Output of `platform create`](platform_create_output.txt)
    - This output uses the project name `my_deployed_blog` to be clearly distinct from the name `blog`, originally used with the `startproject` command.
- [Output of `platform project:info`](platform_project_info_output.txt)
    - This is the output after the `platform create` call, captured in [platform_create_output.txt](platform_create_output.txt).
- [Output of `platform help project:create`](platform_create_help.txt)
    - This command is used in implementing `--automate-all`, and is helpful to have as a reference.
- [Output of `platform organization:info`](platform_organization_info.txt)
    - This command is used when running `--automate-all`. Contains fake id value.
- [Output of `platform help push`](platform_push_help.txt)
    - Used in `--automate-all`, helpful to have as a reference.