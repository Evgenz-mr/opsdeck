# OpsDeck

**Self-service operations portal for engineering teams.**

> Environment health, diagnostics and safe operations.

Русская документация: [docs/README_RU.md](docs/README_RU.md)  
English documentation: [docs/README_EN.md](docs/README_EN.md)

Запуск через Podman Compose: [docs/PODMAN_COMPOSE_RU.md](docs/PODMAN_COMPOSE_RU.md)

Deployment guide RU: [docs/DEPLOYMENT_RU.md](docs/DEPLOYMENT_RU.md)  
Deployment guide EN: [docs/DEPLOYMENT_EN.md](docs/DEPLOYMENT_EN.md)

## What OpsDeck is

OpsDeck is a containerized operational portal for developers, QA engineers and DevOps teams.

It provides a safe interface for:

- VM operations over SSH;
- Kubernetes health across DEV / STABLE / SANDBOX / IFT;
- VictoriaMetrics cluster checks;
- Kafka broker/exporter health;
- PostgreSQL node/role health;
- S3 endpoint/TLS health;
- certificate inspection and allowlisted renewal actions;
- rolling operations and preflight safety policies;
- guided diagnostics and runbooks;
- realtime execution events through SSE;
- service catalog, dependency helpers, incident timeline and maintenance mode;
- RBAC policy foundations, notifications and audit history.

Arbitrary shell access is intentionally not part of the product.

## Architecture

```text
Users
  |
  v
OpsDeck UI / REST API / SSE
  |
  +-- Kubernetes API
  +-- SSH allowlisted actions
  +-- VictoriaMetrics
  +-- Kafka
  +-- PostgreSQL
  +-- S3
  |
  v
Health / Actions / Runbooks / Safety / Audit
```

Approvals are implemented as a configuration concept but disabled by default:

```yaml
approvals:
  enabled: false
```

Safety policies work independently of approvals.

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

Health endpoint:

```text
GET /healthz
```

## Branch model

```text
main
  ^
release/1.0.0
  ^
develop
```

`develop` is the integration branch. `release/1.0.0` is the deployment candidate. `main` stays stable until the release is accepted.

## Project status

Current release candidate: **1.0.0**

The first release is intended for controlled internal deployment. Start with read-only health checks, then enable allowlisted VM actions after inventory, SSH permissions and safety policies are verified.
