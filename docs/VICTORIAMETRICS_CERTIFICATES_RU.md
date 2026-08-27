# VictoriaMetrics: диагностика и обновление сертификатов

OpsDeck описывает IFT-кластер из трёх узлов:

| Узел | Компонент | systemd unit |
|---|---|---|
| `vm-szux-pc-vic-193.vdc03.pc.dev.sbt` | vminsert | `vminsert.service` |
| `vm-szux-pc-vic-194.vdc03.pc.dev.sbt` | vmselect | `vmselect.service` |
| `vm-szux-pc-vic-195.vdc03.pc.dev.sbt` | vmstorage | `vmstorage.service` |

На каждом узле OpsDeck может проверить systemd-сервис, прочитать метаданные
сертификата `/opt/victoria-metrics/certs/tls.crt` и запустить фиксированный
root-owned wrapper обновления сертификата.

OpsDeck не принимает произвольную shell-команду от пользователя. Action ID,
команда, host и SSH user находятся в репозитории и проходят allowlist-проверку.
Операции одного VictoriaMetrics-кластера выполняются последовательно и
записываются в SQLite audit log.

Карточка кластера автоматически показывает только состояние systemd-сервиса,
дату окончания сертификата и оставшееся количество дней. Статусы вычисляются
от текущего UTC-времени: `healthy` от 30 дней, `warning` от 10 до 29 дней,
`critical` менее 10 дней, `expired` после окончания и `invalid`, если срок
действия ещё не начался.

## 1. Отдельный SSH-пользователь на трёх узлах

На каждом VictoriaMetrics-узле выполните от root:

```bash
useradd --system --create-home --shell /bin/bash opsdeck
install -d -o opsdeck -g opsdeck -m 0700 /home/opsdeck/.ssh
```

Не используйте для портала персонального пользователя или root SSH.

Проверьте и защитите существующий скрипт:

```bash
chown root:root /home/user_szux-ift/secman_certs.sh
chmod 0750 /home/user_szux-ift/secman_certs.sh
```

Установите root-owned wrapper. Он задаёт рабочий каталог скрипта, чтобы
относительные ссылки на `payload.json` и другие соседние файлы работали так же,
как при ручном запуске из `/home/user_szux-ift`:

```bash
install -o root -g root -m 0755 \
  deploy/victoriametrics/opsdeck-renew-vm-cert \
  /usr/local/sbin/opsdeck-renew-vm-cert
```

Скрипт не должен принимать пользовательские аргументы, читать команды из
окружения или выводить токены и приватный ключ сертификата в stdout/stderr.

## 2. Ограниченный sudo

Скопируйте `deploy/victoriametrics/opsdeck-sudoers` на каждый узел:

```bash
install -o root -g root -m 0440 \
  deploy/victoriametrics/opsdeck-sudoers \
  /etc/sudoers.d/opsdeck-victoriametrics

visudo -cf /etc/sudoers.d/opsdeck-victoriametrics
```

Разрешены только две точные команды:

```text
/usr/local/sbin/opsdeck-renew-vm-cert
/usr/bin/openssl x509 -in /opt/victoria-metrics/certs/tls.crt -noout -subject -issuer -serial -dates
```

Произвольный `sudo`, shell, restart сервисов и чтение `tls.key` не разрешены.

## 3. SSH-ключ OpsDeck

На VM с OpsDeck:

```bash
install -d -o 10001 -g 100 -m 0700 /etc/opsdeck/ssh

ssh-keygen -t ed25519 \
  -f /etc/opsdeck/ssh/id_ed25519 \
  -N '' \
  -C opsdeck-victoriametrics

chown 10001:100 /etc/opsdeck/ssh/id_ed25519*
chmod 0400 /etc/opsdeck/ssh/id_ed25519
chmod 0444 /etc/opsdeck/ssh/id_ed25519.pub
```

Установите публичный ключ в `/home/opsdeck/.ssh/authorized_keys` на всех трёх
узлах. На каждом целевом узле:

```bash
install -o opsdeck -g opsdeck -m 0600 \
  /tmp/opsdeck_id_ed25519.pub \
  /home/opsdeck/.ssh/authorized_keys
```

Соберите host keys на VM с OpsDeck:

```bash
ssh-keyscan -H \
  vm-szux-pc-vic-193.vdc03.pc.dev.sbt \
  vm-szux-pc-vic-194.vdc03.pc.dev.sbt \
  vm-szux-pc-vic-195.vdc03.pc.dev.sbt \
  > /etc/opsdeck/ssh/known_hosts

chown 10001:100 /etc/opsdeck/ssh/known_hosts
chmod 0400 /etc/opsdeck/ssh/known_hosts
```

До запуска обязательно сравните отпечатки `ssh-keygen -lf` с отпечатками,
полученными через доверенный канал. OpsDeck не использует `known_hosts=None`.

Проверьте подключения:

```bash
ssh -i /etc/opsdeck/ssh/id_ed25519 \
  -o UserKnownHostsFile=/etc/opsdeck/ssh/known_hosts \
  opsdeck@vm-szux-pc-vic-193.vdc03.pc.dev.sbt \
  /usr/bin/systemctl is-active vminsert.service
```

Повторите для vmselect и vmstorage.

## 4. Operator token

На VM с OpsDeck создайте отдельный токен действий:

```bash
openssl rand -hex 32 > /etc/opsdeck/action-token
chown 10001:100 /etc/opsdeck/action-token
chmod 0400 /etc/opsdeck/action-token
```

В `.env` хранятся только пути, не секреты:

```dotenv
OPSDECK_ACTION_TOKEN_FILE_HOST=/etc/opsdeck/action-token
OPSDECK_SSH_DIR_HOST=/etc/opsdeck/ssh
```

## 5. Проверка до запуска из UI

Проверка сертификата от имени `opsdeck`:

```bash
ssh -i /etc/opsdeck/ssh/id_ed25519 \
  -o UserKnownHostsFile=/etc/opsdeck/ssh/known_hosts \
  opsdeck@vm-szux-pc-vic-193.vdc03.pc.dev.sbt \
  '/usr/bin/sudo -n /usr/bin/openssl x509 -in /opt/victoria-metrics/certs/tls.crt -noout -subject -issuer -serial -dates'
```

Тест обновления сначала выполняйте только на одном согласованном узле:

```bash
ssh -i /etc/opsdeck/ssh/id_ed25519 \
  -o UserKnownHostsFile=/etc/opsdeck/ssh/known_hosts \
  opsdeck@vm-szux-pc-vic-193.vdc03.pc.dev.sbt \
  '/usr/bin/sudo -n /usr/local/sbin/opsdeck-renew-vm-cert'
```

После этого проверьте дату сертификата и состояние компонента.

## 6. Безопасный доступ к web console

Action-кнопки отключены при открытии OpsDeck по обычному HTTP с удалённого ПК,
поскольку operator token нельзя передавать открытым текстом. Используйте HTTPS
через reverse proxy или SSH-туннель:

```bash
ssh -L 8080:127.0.0.1:8080 <vm-user>@vm-szux-pc-docker-185.vdc03.pc.dev.sbt
```

Затем откройте `http://127.0.0.1:8080`, введите operator token и запускайте
действие только для одного узла за раз.
