# OpsDeck — инструкция на русском

OpsDeck — self-service operations portal для разработчиков, тестировщиков и DevOps.

Главная идея: команда получает безопасную диагностику и заранее разрешённые действия без прямого SSH-доступа.

## Возможности MVP

- стенды DEV / STABLE / SANDBOX / IFT;
- подключение разрешённых Kubernetes namespace;
- состояние Deployments и Pods;
- выполнение только allowlist SSH-actions;
- принудительное обновление сертификата на выбранных VM;
- audit history в SQLite;
- YAML runbooks;
- каркас интеграций VictoriaMetrics, Kafka, PostgreSQL и S3.

## Запуск

```bash
git clone https://github.com/Evgenz-mr/opsdeck.git
cd opsdeck
docker compose up -d --build
```

UI: `http://localhost:8080`

Swagger: `http://localhost:8080/docs`

## Конфигурация стендов

Файл `config/opsdeck.yaml`:

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

Action хранится в `actions/`:

```yaml
id: update-certificate
name: Force TLS certificate update
risk: caution
runner: ssh
timeout: 180
command: sudo /opt/scripts/update-cert.sh
```

На VM рекомендуется отдельный пользователь `opsdeck` и точечное sudo правило:

```text
opsdeck ALL=(root) NOPASSWD: /opt/scripts/update-cert.sh
```

Не используйте `NOPASSWD: ALL`.

## Approvals

Функция заложена, но по умолчанию выключена:

```yaml
approvals:
  enabled: false
```

## Kubernetes health

Endpoint:

```text
GET /api/health/kubernetes/{environment}/{namespace}
```

Проверяются readiness Deployment, phase Pod, restart count и waiting reasons вроде CrashLoopBackOff.

## Что добавлять дальше

1. Realtime SSE/WebSocket logs
2. Rolling actions по группам VM
3. Certificate Center
4. Native Kafka adapter: brokers, partitions, consumer lag
5. Native PostgreSQL adapter: primary/replica, replication lag, locks, long queries
6. S3 synthetic PUT/GET/DELETE в `.opsdeck-health/`
7. VictoriaMetrics topology health
8. Guided diagnostics и incident report
9. RBAC + Keycloak/OIDC
10. Environment comparison DEV/STABLE/IFT/SANDBOX
