# OpsDeck 1.0.0 — deployment guide

This guide is for the first controlled internal deployment of OpsDeck.

## 1. Recommended rollout order

Start with read-only features:

1. Web UI and `/healthz`;
2. Kubernetes health;
3. VictoriaMetrics/Kafka/PostgreSQL/S3 health;
4. Certificate Center inspection;
5. enable SSH actions only after the read-only layer is verified.

Approvals remain disabled initially:

```yaml
approvals:
  enabled: false
```

Preflight safety and RBAC should be enforced independently of approvals.

## 2. Requirements

The OpsDeck host needs:

- Docker Engine;
- Docker Compose plugin;
- network access to Kubernetes API endpoints and managed services;
- kubeconfig with least-privilege access;
- a dedicated SSH key for the OpsDeck user;
- DNS/routing to target VMs.

## 3. Clone the release branch

```bash
git clone https://github.com/Evgenz-mr/opsdeck.git
cd opsdeck
git checkout release/1.0.0
```

## 4. Kubernetes configuration

Inspect available contexts:

```bash
kubectl config get-contexts
```

Update `config/opsdeck.yaml` with the real contexts for:

```text
DEV
STABLE
SANDBOX
IFT
```

and define the namespace allowlists.

For the first rollout, prefer read-only ServiceAccount/Role/RoleBinding permissions.

## 5. VM inventory

Replace sample addresses in `config/opsdeck.yaml` with real hostnames/IPs.

Example:

```yaml
services:
  victoriametrics:
    targets:
      stable:
        vmselect-01:
          host: vmselect-01.example.internal
          user: opsdeck
          tls_port: 443
          actions:
            - check-service
            - check-certificate
            - update-certificate
```

## 6. Dedicated SSH user

Use a dedicated `opsdeck` user on target VMs.

Do not grant unrestricted sudo access. Allow only explicitly approved scripts, for example:

```text
opsdeck ALL=(root) NOPASSWD: /opt/scripts/update-cert.sh
```

Never use:

```text
NOPASSWD: ALL
```

## 7. Verify SSH before enabling actions

From the OpsDeck host:

```bash
ssh -i ~/.ssh/id_opsdeck opsdeck@vmselect-01 'hostname'
```

Then test the allowlisted script separately if it supports a safe help/test mode.

## 8. Start OpsDeck

```bash
docker compose config
docker compose build
docker compose up -d
```

Verify:

```bash
docker compose ps
docker compose logs --tail=200 opsdeck
curl http://127.0.0.1:8080/healthz
```

Expected:

```json
{"status":"ok","version":"1.0.0"}
```

Swagger UI:

```text
http://SERVER:8080/docs
```

## 9. Kubernetes health

Example:

```text
GET /api/health/kubernetes/stable/payments
```

Verify read access first and confirm that the initial kube credentials cannot mutate resources.

## 10. Service health adapters

After adding health configuration, test:

```text
GET /api/victoriametrics/{environment}
GET /api/kafka/{environment}
GET /api/postgres/{environment}
GET /api/s3/{environment}
```

## 11. Certificate Center

Before the first renewal, use inspection only:

```text
GET /api/certificates/{service}/{environment}/{target}
```

Validate expiry date, server name, TLS port and target reachability.

Only then test `update-certificate`, starting in DEV/SANDBOX.

## 12. First action test

Do not start with an entire cluster.

Recommended order:

1. one test VM;
2. DEV/SANDBOX;
3. `check-service`;
4. `check-certificate`;
5. `update-certificate`;
6. verify audit history;
7. verify service health after the operation;
8. then test a rolling action on a group.

## 13. Security acceptance

Before team use, confirm:

- no arbitrary shell is exposed;
- SSH user has minimal sudo permissions;
- kubeconfig is least privilege;
- secrets are not committed to Git;
- production actions are policy restricted;
- preflight blocks unsafe selected-node ratios;
- logs do not expose secret values.

## 14. Backup

Back up the `opsdeck-data` Docker volume containing the SQLite audit database.

Example:

```bash
docker run --rm \
  -v opsdeck_opsdeck-data:/data:ro \
  -v "$PWD/backup":/backup \
  alpine sh -c 'cp /data/opsdeck.db /backup/opsdeck-$(date +%F-%H%M).db'
```

## 15. Rollback OpsDeck

Record the known-good Git SHA before upgrades.

Rollback:

```bash
git checkout <known-good-sha>
docker compose build
docker compose up -d
```

The audit database is stored in a persistent volume, so replacing the application container should not remove operation history.

## 16. First acceptance checklist

The release is ready for broader internal use after:

- CI is green;
- container survives/restarts after host reboot;
- Kubernetes health works for all four environments;
- health adapters work against at least one real environment;
- certificate inspection reports correct data;
- certificate update succeeds on one test VM;
- rolling execution stops on a simulated failure;
- audit history records the operation;
- an unauthorized action is denied;
- SQLite backup/restore is tested.
