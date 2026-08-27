# PostgreSQL health adapter

The first adapter checks node reachability, expected roles and optional exporter availability without exposing destructive actions.

Next checks:

- direct SQL `pg_is_in_recovery()` role verification;
- replication lag;
- connection saturation;
- long-running queries;
- blocking locks;
- disk usage;
- TLS expiry.

High-risk actions such as failover and primary restart are intentionally excluded from developer actions.
