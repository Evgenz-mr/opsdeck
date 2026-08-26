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
