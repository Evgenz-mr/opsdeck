# OpsDeck — English guide

OpsDeck is a self-service operations portal for developers, QA engineers and DevOps teams.

The goal is to provide safe diagnostics and predefined operational actions without direct SSH access.

## MVP capabilities

- DEV / STABLE / SANDBOX / IFT environments;
- allowed Kubernetes namespaces;
- Deployment and Pod health;
- allowlisted SSH actions only;
- forced certificate update on selected VMs;
- SQLite audit history;
- YAML runbooks;
- integration skeletons for VictoriaMetrics, Kafka, PostgreSQL and S3.

## Start

```bash
git clone https://github.com/Evgenz-mr/opsdeck.git
cd opsdeck
docker compose up -d --build
```

UI: `http://localhost:8080`

Swagger: `http://localhost:8080/docs`

## Environment configuration

Edit `config/opsdeck.yaml`:

```yaml
environments:
  stable:
    kubernetes:
      context: stable
      namespaces:
        - monitoring
        - payments
```

## Actions as Code

Actions live under `actions/`:

```yaml
id: update-certificate
name: Force TLS certificate update
risk: caution
runner: ssh
timeout: 180
command: sudo /opt/scripts/update-cert.sh
```

Use a dedicated `opsdeck` SSH account and a narrow sudoers rule:

```text
opsdeck ALL=(root) NOPASSWD: /opt/scripts/update-cert.sh
```

Do not grant `NOPASSWD: ALL`.

## Approvals

Approval support is modeled but disabled initially:

```yaml
approvals:
  enabled: false
```

## Kubernetes health

Endpoint:

```text
GET /api/health/kubernetes/{environment}/{namespace}
```

Current checks cover Deployment readiness, Pod phase, restart counts and waiting reasons such as CrashLoopBackOff.

## Planned roadmap

1. Realtime SSE/WebSocket logs
2. Rolling actions across VM groups
3. Certificate Center
4. Native Kafka adapter: brokers, partitions, consumer lag
5. Native PostgreSQL adapter: primary/replica, replication lag, locks, long queries
6. S3 synthetic PUT/GET/DELETE under `.opsdeck-health/`
7. VictoriaMetrics topology health
8. Guided diagnostics and incident reports
9. RBAC + Keycloak/OIDC
10. DEV/STABLE/IFT/SANDBOX comparison
