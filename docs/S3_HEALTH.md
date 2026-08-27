# S3 health adapter

The initial adapter validates endpoint availability and TLS connectivity.

The production adapter should add a synthetic object probe under a dedicated prefix such as `.opsdeck-health/`:

1. PUT a random small object;
2. GET and compare it;
3. DELETE it;
4. record latency;
5. never touch application objects.

Credentials must be provided through runtime secrets, never committed to repository configuration.
