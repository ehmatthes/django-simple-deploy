Platform notes: Fly.io
---

For now, this is an informal collection of useful notes about supporting deployment to Fly.io.

Documentation
---

- [Fly docs](https://fly.io/)
- [Fly apps](https://fly.io/docs/reference/apps/)
- [Launch a New App on Fly.io](https://fly.io/docs/apps/launch/)
    - We don't use `fly launch`, because it's not meant to be scripted. But there is sometimes useful information here.
- Regions
    - `fly platform regions` [command](https://fly.io/docs/flyctl/platform-regions/)
    - `fly regions` [command](https://fly.io/docs/flyctl/regions/), mostly deprecated
- `fly apps create` [command](https://fly.io/docs/flyctl/apps-create/)

    
Other resources
---

- Fly CLI [source](https://github.com/superfly/flyctl)