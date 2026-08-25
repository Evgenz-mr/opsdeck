# OpsDeck

**Self-service operations portal for engineering teams.**

> Give your team safe operations, not SSH access.

Русская документация: [docs/README_RU.md](docs/README_RU.md)

English documentation: [docs/README_EN.md](docs/README_EN.md)

## What OpsDeck is

OpsDeck is a containerized operational portal for developers, QA engineers and DevOps teams.

It provides a safe interface for:

- VM operations over SSH;
- Kubernetes health across DEV / STABLE / SANDBOX / IFT;
- VictoriaMetrics operational checks;
- Kafka health and diagnostics;
- PostgreSQL cluster health;
- S3 health checks;
- certificate updates;
- guided runbooks;
- audit history;
- safe predefined actions.

Arbitrary shell access is intentionally not part of the product.

## MVP

```text
Users
  |
  v
OpsDeck UI / API
  |
  +-- Kubernetes API
  +-- SSH actions
  +-- VictoriaMetrics
  +-- Kafka
  +-- PostgreSQL
  +-- S3
  |
  v
Audit / Runbooks / Diagnostics
```

Approvals are implemented as a configuration concept but disabled by default:

```yaml
approvals:
  enabled: false
```

## Quick start

```bash
docker compose up -d --build
```

Open:

```text
http://localhost:8080
```

API documentation:

```text
http://localhost:8080/docs
```

## Project status

Current version: **0.1.0 / MVP**

The initial implementation focuses on architecture, configuration-driven inventory, Kubernetes health, safe SSH actions and audit logging.
