Roadmap
===

Much of the work to this point (1/12/22) has focused on proof-of-concept. The proof of concept work is pretty much complete; this project does everything I hoped it would. It allows simplified deployments on two PAAS platforms that offer Django support. If a bunch of Django teaching resources used this project instead of all referring to the platforms' docs, one change here would save a whole bunch of changes in all those teaching resources. And we can continue to make the initial deployment of learning and demo projects simple and easy for people new to Django.

Current areas of focus:
---

- Refine the Heroku deployment process.
    - Heroku has been the established platform in the PAAS space, and it still works really well. It's also simple, free, and quick to use and to test against.
    - Clarify the API.
    - Clarify the approach to deployment issues such as how to manage the secret key.
    - Polish the documentation:
      - On this repo
      - In the codebase
      - In the output
      - In user-friendly log files.
- When we are happy with the overall Heroku deployment process, we can be more selective about which platform to fully support next.
