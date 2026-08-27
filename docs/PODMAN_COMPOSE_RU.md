# OpsDeck 1.0.0 — запуск через podman-compose

Инструкция рассчитана на rootful Podman 4.9.4 и podman-compose 0.1.7dev.
Все команды `podman`, `podman-compose`, `build`, `up`, `ps` и `logs` необходимо
выполнять одним и тем же пользователем. Для текущей VM это `root`.

## 1. Требования

Проверьте версии и режим:

```bash
podman --version
podman-compose version
podman info --format '{{.Host.Security.Rootless}}'
```

Ожидаемый rootful-режим:

```text
false
```

Команда `podman-compose --version` не поддерживается версией 0.1.7dev.
Используйте `podman-compose version`. Действие `config` в этой версии также
отсутствует.

Версия 0.1.7dev несовместима с сетевой настройкой одиночного контейнера внутри
автоматически созданного Pod на Podman 4.9. Поэтому OpsDeck запускается через
wrapper `scripts/opsdeck-podman-compose`, который экспортирует `.env` и всегда
передает transformation policy `-t identity`. Для одного сервиса этот режим не
создает общий Pod и устраняет конфликт сетевых параметров Podman 4.9.

## 2. Подготовка проекта

Перейдите в каталог, где рядом находятся `podman-compose.yml` и Dockerfile:

```bash
cd /root/opsdeck-release-1.0.0
git checkout release/1.0.0
git pull --ff-only origin release/1.0.0
```

Создайте `.env` из безопасного примера:

```bash
cp .env.example .env
vi .env
```

Укажите абсолютный путь к отдельному kubeconfig OpsDeck:

```dotenv
OPSDECK_KUBECONFIG_HOST=/home/user/.kube/opsdeck-config
OPSDECK_DATA_DIR=/var/lib/opsdeck
```

`.env` должен находиться в корне проекта рядом с `podman-compose.yml`.
Токены и сертификаты в `.env` не добавляются.

Подготовьте постоянный каталог для SQLite audit DB. Контейнер работает с UID
`10001` и GID `100`:

```bash
mkdir -p /var/lib/opsdeck
chown 10001:100 /var/lib/opsdeck
chmod 0750 /var/lib/opsdeck
```

Версия podman-compose 0.1.7dev не понимает volume option `U`, поэтому права
каталога задаются явно на VM, а mount использует только SELinux option `Z`.

## 3. Проверка kubeconfig

```bash
test -f /home/user/.kube/opsdeck-config
kubectl --kubeconfig /home/user/.kube/opsdeck-config \
  --context opsdeck get pods -n dev
```

Контейнер работает с UID `10001` и GID `100`. Для rootful Podman:

```bash
chown 10001:100 /home/user/.kube/opsdeck-config
chmod 0400 /home/user/.kube/opsdeck-config
```

## 4. SELinux

Bind mounts kubeconfig и конфигурации имеют параметр `:Z`. Podman назначит им
приватную SELinux-метку контейнера. Не заменяйте отдельный kubeconfig на mount
всего `/home/user` или всего каталога `.kube`.

Проверить режим SELinux можно командой:

```bash
getenforce 2>/dev/null || true
```

## 5. Проверка конфигурации стендов

Один kube-context `opsdeck` используется всеми четырьмя стендами. Allowlist
ограничивает каждый стенд его namespace:

```yaml
environments:
  dev:
    kubernetes:
      mode: kubeconfig
      context: opsdeck
      namespaces: [dev]
  stable:
    kubernetes:
      mode: kubeconfig
      context: opsdeck
      namespaces: [stable]
  sandbox:
    kubernetes:
      mode: kubeconfig
      context: opsdeck
      namespaces: [sandbox]
  ift:
    kubernetes:
      mode: kubeconfig
      context: opsdeck
      namespaces: [ift]
```

Если реальные namespaces называются иначе, измените только значения в списках
`namespaces` в `config/opsdeck.yaml`.

## 6. Конфликт с Docker

Docker и Podman не могут одновременно занять порт `8080`. Проверьте Docker:

```bash
docker ps --filter publish=8080
```

Если старая версия OpsDeck запущена через Docker, остановите её, но пока не
удаляйте:

```bash
docker stop opsdeck
```

## 7. Сборка и запуск

Версия podman-compose 0.1.7dev не имеет команды `config`, поэтому начинайте с
проверки подстановки пути:

```bash
grep '^OPSDECK_KUBECONFIG_HOST=' .env
grep '^OPSDECK_DATA_DIR=' .env
test -f "$(sed -n 's/^OPSDECK_KUBECONFIG_HOST=//p' .env)"
test -d "$(sed -n 's/^OPSDECK_DATA_DIR=//p' .env)"
```

Если предыдущая попытка уже создала пустой Pod, удалите только его:

```bash
podman pod ps -a
podman pod rm -f opsdeckrelease100
```

При первом запуске команда удаления может вернуть `no such pod` — это означает,
что очищать нечего.

Сборка:

```bash
./scripts/opsdeck-podman-compose build
```

Запуск:

```bash
./scripts/opsdeck-podman-compose up -d
```

Проверка:

```bash
./scripts/opsdeck-podman-compose ps
podman logs --tail=200 opsdeck
curl -sS http://127.0.0.1:8080/healthz
```

Ожидаемый health:

```json
{"status":"ok","version":"1.0.0"}
```

## 8. Проверка mounts и Kubernetes

```bash
podman inspect opsdeck \
  --format '{{range .Mounts}}{{println .Source "->" .Destination}}{{end}}'
```

Проверьте наличие kubeconfig внутри контейнера:

```bash
podman exec opsdeck ls -ln /home/opsdeck/.kube/config
```

Проверьте Kubernetes diagnostics:

```bash
curl -sS http://127.0.0.1:8080/api/health/kubernetes/dev/dev \
  | python3 -m json.tool
```

Состояние `healthy` или `degraded` означает, что Kubernetes API доступен.
Состояние `unknown` содержит поле `error`, по которому нужно продолжать
диагностику.

## 9. Управление

```bash
./scripts/opsdeck-podman-compose logs
./scripts/opsdeck-podman-compose restart
./scripts/opsdeck-podman-compose stop
./scripts/opsdeck-podman-compose start
```

Для автоматического восстановления rootful-контейнеров после перезагрузки VM:

```bash
systemctl enable --now podman-restart.service
```

Проверьте:

```bash
systemctl status podman-restart.service --no-pager
```

## 10. Откат

Если Podman-версия не стартовала, остановите её:

```bash
./scripts/opsdeck-podman-compose down
```

Затем можно вернуть ранее остановленный Docker-контейнер:

```bash
docker start opsdeck
```

Каталог `/var/lib/opsdeck` и audit DB не удаляются командой `down`.
