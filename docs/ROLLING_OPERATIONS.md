# Rolling operations

Rolling execution is intended for clustered services such as VictoriaMetrics, Kafka and PostgreSQL replicas.

Behavior:

- explicit target list;
- configurable batch size;
- optional pause between batches;
- stop immediately when any target fails;
- remaining targets are not modified;
- each target result can be persisted to audit history.

Default recommendation is `batch_size: 1` for stateful clustered services.
