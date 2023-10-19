---
title: Integration Tests
hide:
    - footer
---

These tests recreate the exact steps we expect users to take on their own system, ending in a live deployment to the platform that's being tested.

Each test makes a copy of the sample project, runs `simple_deploy`, and makes a full deployment. If you want to run these tests, you'll need an account on the platform you're testing against. The test will create an app under your account, and it should prompt you to destroy that app if the test runs successfully. If the test script fails, it may exit before destroying some deployed resources. **You should verify that the app and any related resources were actually destroyed, because these resources will almost certainly accrue charges on your account.**

These would be better referred to as end-to-end tests, and one of the pre-1.0 tasks is to update the names of the different kinds of tests in this project to more accurately reflect what they actually do.

