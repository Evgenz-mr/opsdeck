# Operations Dashboard

The dashboard aggregates environment and Kubernetes namespace health for DEV, STABLE, SANDBOX and IFT.

API:

```text
GET /api/operations/overview
```

The endpoint is intentionally read-only. Action execution remains behind explicit allowlisted actions.

## Next UI widgets

- environment health summary;
- attention queue;
- recent operations;
- certificate warnings;
- dependency health;
- links to runbooks and diagnostics.
