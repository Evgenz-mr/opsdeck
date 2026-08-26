# VictoriaMetrics health adapter

Model cluster components explicitly: vmselect, vminsert, vmstorage and vmagent.

Each component gets a health endpoint and can later be connected to:

- disk usage checks;
- ingestion rate checks;
- internal TCP connectivity;
- certificate state;
- rolling certificate update;
- rolling restart with stop-on-failure behavior.

Example configuration:

```yaml
health:
  stable:
    components:
      - name: vmselect-01
        health_url: http://vmselect-01:8481/health
```
