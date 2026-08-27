# Kubernetes health

Extended namespace health covers:

- Deployments;
- StatefulSets;
- Pods and restart counts;
- waiting reasons such as CrashLoopBackOff;
- Jobs;
- PVC state;
- HPA current/desired replicas;
- PDB disruption availability;
- recent Warning events.

This remains read-only. Mutating Kubernetes actions should be separate allowlisted actions with preflight checks.

## Connection mode

The default deployment reads a dedicated kubeconfig from:

```text
/home/opsdeck/.kube/config
```

Set the host file in `.env` without committing credentials:

```dotenv
OPSDECK_KUBECONFIG_HOST=./secrets/kubeconfig
```

Each environment in `config/opsdeck.yaml` selects one context and explicitly
allowlists its namespaces. OpsDeck creates a separate Kubernetes API client per
request, so concurrent requests to different environments do not share a
global context.

For an in-cluster deployment, set `mode: incluster`. In this mode the context
value is ignored and the pod's ServiceAccount is used.

## Read-only RBAC

Create the ServiceAccount once in every connected cluster:

```bash
kubectl apply -f deploy/kubernetes/service-account.yaml
```

Apply the namespaced Role and RoleBinding only to namespaces that OpsDeck may
diagnose:

```bash
kubectl -n monitoring apply -f deploy/kubernetes/diagnostics-rbac.yaml
kubectl -n payments apply -f deploy/kubernetes/diagnostics-rbac.yaml
kubectl -n integration apply -f deploy/kubernetes/diagnostics-rbac.yaml
```

Verify access before creating the kubeconfig:

```bash
kubectl auth can-i list pods \
  -n payments \
  --as=system:serviceaccount:opsdeck:opsdeck

kubectl auth can-i get secrets \
  -n payments \
  --as=system:serviceaccount:opsdeck:opsdeck
```

The expected results are `yes` for pods and `no` for secrets. The supplied
role contains no write verbs and no permission to read Secrets or ConfigMaps.

## Kubeconfig handling

Use your platform's supported short-lived token or workload identity for the
`opsdeck` ServiceAccount. Token lifetime and renewal depend on cluster policy.
Do not mount an administrator kubeconfig into OpsDeck.

For the initial test, build a dedicated kubeconfig from the ServiceAccount.
Run the helper once per source cluster/context. The second argument is the
context name expected by `config/opsdeck.yaml`:

```bash
mkdir -p secrets
./scripts/add-kubeconfig-context.sh <real-dev-context> dev secrets/kubeconfig
./scripts/add-kubeconfig-context.sh <real-stable-context> stable secrets/kubeconfig
./scripts/add-kubeconfig-context.sh <real-sandbox-context> sandbox secrets/kubeconfig
./scripts/add-kubeconfig-context.sh <real-ift-context> ift secrets/kubeconfig
sudo chown 10001:100 secrets/kubeconfig
sudo chmod 0400 secrets/kubeconfig
```

UID `10001` and GID `100` belong to the `opsdeck:users` process inside the
container. These ownership settings let OpsDeck read the bind-mounted file
without making its token readable to other host users.

The helper requests a 24-hour token by default. Override the requested duration
for testing with `OPSDECK_TOKEN_DURATION=8h`; the API server may cap it. Before
team use, connect the organization's supported renewable authentication method
instead of relying on an unattended static token.

Before starting OpsDeck, verify the dedicated file directly:

```bash
kubectl --kubeconfig ./secrets/kubeconfig config get-contexts
kubectl --kubeconfig ./secrets/kubeconfig \
  --context stable \
  auth can-i list pods -n payments
```

## API check

After `docker compose up -d`, request an allowlisted namespace:

```bash
curl -sS http://127.0.0.1:8080/api/health/kubernetes/stable/payments
```

The response includes Deployments, StatefulSets, Pods, Jobs, PVCs, HPAs, PDBs,
recent Warning events, and a compact object-count summary. Kubernetes requests
have a ten-second timeout.
