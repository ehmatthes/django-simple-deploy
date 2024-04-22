---
title: Unit Tests
hide:
    - footer
---

In the pre-1.0 phase, the codebase is rapidly evolving. Aiming for significant unit test coverage would be quite frustrating at this point.

Unit tests should be written only for the following:

- Specific functions and methods that are critical to current behavior;
- Functions and methods that are likly to be stable beyond 1.0.
- If someone reports a bug, or you find one, definitely consider writing a unit test that prevents that bug from reappearing.

For all unit tests, try to write them in a way that they're not overly dependent on implementation. If you need to change the structure of the project to support that, feel free to suggest that change. For example there's probably a good deal of functionality that can be moved out of a class and into a utility function that's much easier to test in isolation.

Running unit tests
---

```sh
(dsd_env)django-simple-deploy$ pytest tests/unit_tests
```

Running unit and integration tests together
---

Unit tests and integration tests can be run together:

```sh
(dsd_env)django-simple-deploy$ pytest
```

The bare `pytest` command will run all unit and integration tests. It will *not* run end-to-end tests; those tests need to be run explicitly.