# Guided diagnostics

Guided diagnostics turns team knowledge into deterministic runbooks.

The engine receives observations and matches explicit rules. It does not invent commands or execute arbitrary shell.

Example use cases:

- metrics missing;
- Kafka lag growing;
- PostgreSQL replication degraded;
- S3 unavailable;
- certificate problem;
- Kubernetes application unavailable.

The output contains evidence, severity and an optional allowlisted recommended action.
