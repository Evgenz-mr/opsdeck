# Preflight safety

Every mutating cluster action should pass a safety policy before execution.

Examples:

- do not restart all vmstorage nodes;
- do not touch enough Kafka brokers to lose quorum;
- do not restart PostgreSQL primary as a developer action;
- require a minimum number of healthy nodes after the selected batch;
- limit selected fraction of a cluster.

Preflight is independent from approvals. Approvals may remain disabled while hard safety guards still block dangerous operations.
