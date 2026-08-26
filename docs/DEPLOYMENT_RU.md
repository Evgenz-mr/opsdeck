# OpsDeck 1.0.0 — развертывание

Эта инструкция предназначена для первого контролируемого развертывания OpsDeck внутри команды.

## 1. Рекомендуемый порядок

Начинайте с read-only функций:

1. Web UI и `/healthz`;
2. Kubernetes health;
3. VictoriaMetrics/Kafka/PostgreSQL/S3 health;
4. Certificate Center в режиме проверки;
5. только после этого включайте SSH actions.

Approvals пока остаются выключенными:

```yaml
approvals:
  enabled: false
```

Preflight safety и RBAC необходимо использовать независимо от approvals.

## 2. Требования

На VM, где будет запущен OpsDeck:

- Docker Engine;
- Docker Compose plugin;
- сетевой доступ до Kubernetes API и управляемых сервисов;
- kubeconfig с минимально необходимыми правами;
- отдельный SSH key для пользователя OpsDeck;
- DNS/маршрутизация до целевых VM.

## 3. Клонирование release branch

```bash
git clone https://github.com/Evgenz-mr/opsdeck.git
cd opsdeck
git checkout release/1.0.0
```

## 4. Настройка Kubernetes

Проверьте contexts:

```bash
kubectl config get-contexts
```

В `config/opsdeck.yaml` укажите реальные contexts для:

```text
DEV
STABLE
SANDBOX
IFT
```

и allowlist namespaces.

Для первого запуска используйте read-only ServiceAccount/Role/RoleBinding там, где это возможно.

## 5. Настройка VM inventory

В `config/opsdeck.yaml` замените тестовые IP/hostname на реальные значения.

Пример:

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

## 6. Отдельный SSH пользователь

Рекомендуется отдельный пользователь `opsdeck` на целевых VM.

Он не должен иметь общий root shell через sudo.

Разрешайте только конкретные скрипты, например:

```text
opsdeck ALL=(root) NOPASSWD: /opt/scripts/update-cert.sh
```

Не используйте:

```text
NOPASSWD: ALL
```

## 7. Проверка SSH до запуска actions

С хоста OpsDeck:

```bash
ssh -i ~/.ssh/id_opsdeck opsdeck@vmselect-01 'hostname'
```

Затем отдельно проверьте разрешенный скрипт:

```bash
ssh -i ~/.ssh/id_opsdeck opsdeck@vmselect-01 'sudo /opt/scripts/update-cert.sh --help'
```

если ваш скрипт поддерживает безопасный test/help режим.

## 8. Запуск

```bash
docker compose config
docker compose build
docker compose up -d
```

Проверка:

```bash
docker compose ps
docker compose logs --tail=200 opsdeck
curl http://127.0.0.1:8080/healthz
```

Ожидается:

```json
{"status":"ok","version":"1.0.0"}
```

Swagger:

```text
http://SERVER:8080/docs
```

## 9. Проверка Kubernetes

Пример:

```text
GET /api/health/kubernetes/stable/payments
```

Сначала убедитесь, что OpsDeck умеет читать нужные namespaces, но не изменять ресурсы.

## 10. Проверка сервисов

После добавления health configuration проверьте:

```text
GET /api/victoriametrics/{environment}
GET /api/kafka/{environment}
GET /api/postgres/{environment}
GET /api/s3/{environment}
```

## 11. Certificate Center

До первого renewal используйте только inspection:

```text
GET /api/certificates/{service}/{environment}/{target}
```

Проверьте:

- текущую дату окончания;
- server name;
- TLS port;
- доступность target.

После этого можно тестировать `update-certificate` сначала на DEV/SANDBOX.

## 12. Первое тестирование actions

Не начинайте со всего кластера.

Рекомендуемый порядок:

1. одна тестовая VM;
2. DEV/SANDBOX;
3. `check-service`;
4. `check-certificate`;
5. `update-certificate`;
6. проверка audit;
7. проверка health после операции;
8. затем rolling operation на группе.

## 13. Проверка безопасности

Перед использованием командой подтвердите:

- arbitrary shell отсутствует;
- SSH user имеет минимальный sudo;
- kubeconfig имеет минимальные права;
- secrets не находятся в Git;
- production actions ограничены policy;
- preflight запрещает опасный процент одновременно выбранных nodes;
- логи не содержат secret values.

## 14. Резервное копирование

Для первой версии обязательно сохраняйте Docker volume `opsdeck-data`, содержащий SQLite audit DB.

Пример:

```bash
docker run --rm \
  -v opsdeck_opsdeck-data:/data:ro \
  -v "$PWD/backup":/backup \
  alpine sh -c 'cp /data/opsdeck.db /backup/opsdeck-$(date +%F-%H%M).db'
```

## 15. Rollback OpsDeck

Перед обновлением фиксируйте Git SHA рабочей версии.

Для возврата:

```bash
git checkout <known-good-sha>
docker compose build
docker compose up -d
```

Поскольку audit DB хранится в volume, пересоздание application container не должно удалять историю.

## 16. Первый production-like acceptance

Release можно считать принятым после проверки:

- CI зеленый;
- container запускается после reboot;
- Kubernetes health работает для всех четырех стендов;
- health adapters работают минимум для одного реального окружения;
- certificate inspection показывает правильные данные;
- обновление сертификата прошло на одной тестовой VM;
- rolling operation останавливается при simulated failure;
- audit сохраняет операцию;
- unauthorized action блокируется;
- backup/restore SQLite проверен.
