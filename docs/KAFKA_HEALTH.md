# Kafka health adapter

Initial adapter provides bootstrap broker TCP checks and optional exporter reachability.

Planned next checks:

- cluster controller metadata;
- offline partitions;
- under-replicated partitions;
- consumer group lag;
- TLS certificate inspection;
- guided diagnostics for high lag.

Configuration example:

```yaml
services:
  kafka:
    health:
      stable:
        brokers:
          - {host: kafka-01, port: 9092}
          - {host: kafka-02, port: 9092}
          - {host: kafka-03, port: 9092}
        exporter_url: http://kafka-exporter:9308/metrics
```
