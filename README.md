<div align="center">

# 🌐 nettop

**Понятная карта твоей сети одной командой • A clear map of your network in one command**

[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![Python: 3.10+](https://img.shields.io/badge/Python-3.10+-3776AB.svg?logo=python&logoColor=white)](pyproject.toml)
[![Platform: Linux · macOS · Windows](https://img.shields.io/badge/Platform-Linux%20%C2%B7%20macOS%20%C2%B7%20Windows-lightgrey.svg)](#)
[![Dependencies: stdlib only](https://img.shields.io/badge/Dependencies-stdlib%20only-brightgreen.svg)](#)
[![PRs Welcome](https://img.shields.io/badge/PRs-welcome-brightgreen.svg)](CONTRIBUTING.md)

[Русский](#-русский) • [English](#-english)

</div>

```
┌───────────────────────────────────────────────────┐
│ Network scan: 192.168.1.0/24                      │
│ 2026-05-18T09:14:02Z  |  8 device(s)  |  8 online │
└───────────────────────────────────────────────────┘

  IP           │ HOSTNAME            │ OS             │ TYPE    │ ST │ PORTS
  ─────────────┼─────────────────────┼────────────────┼─────────┼────┼────────────────────
  192.168.1.1  │ router              │ Network device │ network │ ✓  │ 53, 80, 443
  192.168.1.5  │ db-server           │ Linux/Unix     │ server  │ ✓  │ 22, 5432, 6379
  192.168.1.6  │ web-server          │ Linux/Unix     │ server  │ ✓  │ 22, 80, 443, 9090
  192.168.1.10 │ nas                 │ Linux/Unix     │ server  │ ✓  │ 22, 139, 445, 5000
  192.168.1.20 │ pi-hole             │ Linux/Unix     │ server  │ ✓  │ 53, 80, 22
  192.168.1.30 │ living-room-speaker │ -              │ iot     │ ✓  │ 1400, 1443
  192.168.1.40 │ office-printer      │ -              │ printer │ ✓  │ 631, 9100
  192.168.1.55 │ workstation         │ Windows        │ desktop │ ✓  │ 135, 139, 445, 3389
```

---

## 🇷🇺 Русский

**nettop** сканирует сеть, находит подключённые устройства, определяет их
операционные системы и сервисы, отслеживает трафик между ними и выводит
результат в удобном виде: таблица в терминале, JSON, YAML, CSV, ASCII-граф
топологии, готовая Markdown-документация или метрики Prometheus.

Это принципиально **CLI-first** инструмент. Никакого веб-интерфейса, который
нужно запускать, и никакого сервиса, за которым нужно следить — просто одна
команда, которая встраивается в скрипты, cron, CI и системы мониторинга. Он
работает на одной только стандартной библиотеке, поэтому обычный `pip install`
сразу даёт рабочий инструмент, и настраивать больше ничего не нужно. Если в
системе есть `nmap` и `tcpdump`, nettop использует их для точного определения ОС
и захвата трафика; если их нет — переключается на встроенный сканер и продолжает
работать.

### Зачем это нужно

У большинства администраторов нет полной картины собственной сети: что
подключено, какие порты открыты, кто с кем общается, сколько идёт трафика.
Привычные ответы — либо слишком низкоуровневые, чтобы собрать из них карту
(`nmap`, `tcpdump` по одному хосту), либо слишком тяжёлые, чтобы разворачивать
их ради быстрого взгляда (Zabbix, Nagios), либо завязаны на графический
интерфейс, которого нет на headless-сервере (Wireshark).

nettop закрывает нишу посередине: запустил одну команду — получил понятную карту
сети в формате, с которым реально можно работать. Работает сразу, без
настройки, и сделан для терминала.

### Возможности

- **Обнаружение устройств** — ping-свип вместе с TCP-пробами находит живые хосты,
  включая те, что не отвечают на ICMP. Права root не нужны.
- **Определение портов и сервисов** — продуманный набор портов с опциональным
  снятием баннеров, сопоставленный с понятными именами сервисов.
- **Подсказки по ОС и вендору** — определение семейства ОС по TTL и вендора по
  MAC-адресу из коробки; полный fingerprint при наличии `nmap`.
- **Классификация устройств** — серверы, десктопы, сетевое оборудование, IoT и
  принтеры распознаются автоматически.
- **Семь форматов вывода** — `text`, `json`, `yaml`, `csv`, `ascii`,
  `markdown`, `prometheus`.
- **История и сравнение** — каждое сканирование сохраняется в SQLite; `diff`
  показывает, что именно изменилось между двумя из них.
- **Анализ трафика** — bandwidth по каждому соединению из живого захвата
  `tcpdump`.
- **Режим демона** — периодические сканы, алерты, REST API и эндпоинт
  Prometheus `/metrics`, и всё это на стандартной библиотеке.
- **Честная обработка ошибок** — нет прав, нет утилиты, недоступна сеть —
  выводится понятное сообщение, а не трейсбек.

### Установка

```bash
git clone https://github.com/Sliptval/network-topology-analyzer.git
cd network-topology-analyzer
pip install .
```

> **Свежие Debian/Ubuntu:** если `pip install .` отвечает
> `externally-managed-environment` — это защита PEP 668, системный Python
> нарочно не даёт ставить пакеты напрямую. Проще всего запустить
> `scripts/install.sh` — он сам это обнаружит и поставит nettop в приватный
> venv без участия root. Вручную то же самое: `pipx install .` или
> `python3 -m venv .venv && .venv/bin/pip install .`.

После этого команда `nettop` доступна в PATH. Можно запускать и прямо из
каталога, без установки:

```bash
python -m nettop --help
# или
./nettop-cli --help
```

**Опциональные внешние утилиты.** nettop работает и без них, но с ними собирает
более точные данные:

| Утилита   | Что добавляет                       | Debian/Ubuntu         | macOS               |
| --------- | ----------------------------------- | --------------------- | ------------------- |
| `nmap`    | fingerprint ОС, версии сервисов     | `apt install nmap`    | `brew install nmap` |
| `tcpdump` | захват живого трафика (`--traffic`) | `apt install tcpdump` | предустановлен      |

Проверить окружение можно в любой момент: `nettop doctor`.

### Быстрый старт

```bash
# Сканировать подсеть (если --network не указан, локальная сеть определится сама)
nettop scan --network 192.168.1.0/24

# Более глубокий скан с определением баннеров/версий, сохранённый в JSON
nettop scan --network 192.168.1.0/24 --deep --output json --save scan.json

# Всё, что известно про один хост
nettop device 192.168.1.5 --ports --services

# Нарисовать топологию
nettop visualize

# Сгенерировать документацию сети для вики
nettop export --format markdown --output network-docs.md
```

### Команды

| Команда     | Что делает                                              |
| ----------- | ------------------------------------------------------- |
| `scan`      | Обнаружить устройства, порты и сервисы в сети.          |
| `device`    | Подробная информация об одном хосте (в т.ч. `--history`). |
| `monitor`   | Повторяющиеся сканы с интервалом; сообщает об изменениях. |
| `diff`      | Сравнить два сохранённых скана и показать изменения.    |
| `export`    | Перерисовать последний скан в другом формате.           |
| `visualize` | ASCII-граф топологии последнего скана.                  |
| `trace`     | Трассировка маршрута до хоста.                          |
| `daemon`    | Фоновый мониторинг с алертами и опциональным REST API.  |
| `doctor`    | Проверить окружение, права и опциональные утилиты.      |

Полный список опций любой команды — `nettop <команда> --help`.

`--network` принимает CIDR (`192.168.1.0/24`), диапазон через дефис
(`10.0.0.1-10.0.0.50`), одиночный IP или их сочетание через запятую. Если его не
указать, nettop возьмёт определённую им локальную сеть.

### Форматы вывода

Любой формат доступен и через `scan --output <формат>`, и через
`export --format <формат>`.

<details>
<summary><strong>ASCII-топология</strong> — <code>nettop visualize</code></summary>

```
192.168.1.0/24
└─ [gateway] 192.168.1.1
   ├─ db-server (192.168.1.5) [server]
   │  ├─ os: Linux/Unix
   │  └─ services: SSH, PostgreSQL, Redis
   ├─ web-server (192.168.1.6) [server]
   │  ├─ os: Linux/Unix
   │  └─ services: SSH, HTTP, HTTPS, Prometheus
   ├─ nas (192.168.1.10) [server]
   │  ├─ os: Linux/Unix
   │  └─ services: SSH, NetBIOS, SMB, UPnP/Flask
   └─ workstation (192.168.1.55) [desktop]
      ├─ os: Windows
      └─ services: MSRPC, NetBIOS, SMB, RDP
```
</details>

<details>
<summary><strong>Метрики Prometheus</strong> — <code>--format prometheus</code></summary>

```
# HELP nettop_devices_online Devices currently online.
# TYPE nettop_devices_online gauge
nettop_devices_online{network="192.168.1.0/24"} 8
nettop_device_up{network="192.168.1.0/24",ip="192.168.1.5",hostname="db-server"} 1
nettop_device_open_ports{network="192.168.1.0/24",ip="192.168.1.5"} 3
nettop_bandwidth_mbps{source="192.168.1.6",dest="192.168.1.5",protocol="tcp"} 42.7
```
</details>

<details>
<summary><strong>JSON</strong> — <code>--output json</code></summary>

```json
{
  "scan_timestamp": "2026-05-18T09:14:02Z",
  "network": "192.168.1.0/24",
  "online_count": 8,
  "devices": [
    {
      "ip": "192.168.1.5",
      "hostname": "db-server",
      "os": "Linux/Unix",
      "status": "online",
      "ports": [22, 5432, 6379],
      "services": ["SSH", "PostgreSQL", "Redis"]
    }
  ]
}
```
</details>

В репозитории есть готовый пример скана — `docs/examples/home-lab.json`.
Попробуй на нём экспортёры, ничего не сканируя:

```bash
nettop export --input docs/examples/home-lab.json --format markdown
nettop visualize --input docs/examples/home-lab.json
```

### Режим демона и REST API

Непрерывный мониторинг с алертами и, при желании, небольшим HTTP API:

```bash
nettop daemon --config config/default.yaml
nettop daemon --network 192.168.1.0/24 --interval 5m --api 127.0.0.1:8080
```

API построен на стандартной библиотеке — без фреймворка и лишних зависимостей:

| Эндпоинт                | Отдаёт                              |
| ----------------------- | ----------------------------------- |
| `GET /api/status`       | Сводку по демону и последнему скану |
| `GET /api/devices`      | Все устройства из последнего скана  |
| `GET /api/devices/<ip>` | Одно устройство                     |
| `GET /api/traffic`      | Наблюдаемые соединения              |
| `GET /api/alerts`       | Активные алерты                     |
| `GET /metrics`          | Метрики в формате Prometheus        |

Алерты срабатывают, когда устройство ушло в офлайн, появилось новое устройство,
соединение превысило порог по bandwidth или задержка выросла выше лимита — всё
это настраивается в YAML-конфиге ([`config/default.yaml`](config/default.yaml)).
Запуск как systemd-сервис — `scripts/setup-daemon.sh`.

### Как это устроено

```
nettop/
├── cli.py            Разбор команд; превращает ошибки в понятные сообщения
├── models.py         Device, Connection, Alert, ScanResult — общий словарь данных
├── services.py       Порт → имя сервиса и эвристики типа устройства
├── scanner/          Обнаружение хостов, сканирование портов, опциональный nmap
├── traffic/          Захват через tcpdump и bandwidth по соединениям
├── storage/          Хранилище истории на SQLite
├── export/           По одному модулю на формат вывода, за небольшим реестром
├── daemon/           Цикл мониторинга, правила алертов и REST API
└── utils/            Разбор адресов, ARP/вендоры, права, логирование
```

Каждый этап работает с одними и теми же dataclass-ами, поэтому сканер, база и
экспортёры говорят на одном языке. Обнаружение и сканирование портов идут в
пулах потоков; `/24` обычно проходит за несколько секунд, даже если бо́льшая
часть адресов не отвечает.

### Требования

- **Python 3.10 или новее.** Обязательных сторонних пакетов нет.
- Опционально: `pyyaml` для более аккуратного YAML; `nmap` для определения
  ОС/версий; `tcpdump` для захвата трафика.
- Сканирование работает без прав root. Fingerprint ОС и захват трафика требуют
  root/Администратора; nettop проверяет это и сообщает, когда прав не хватает.

### Разработка

```bash
pip install -e ".[dev]"
pytest
```

### Ответственное использование

Сканируй только те сети, которыми владеешь или на тестирование которых у тебя
есть разрешение. Подробнее — [docs/legal.md](docs/legal.md).

---

## 🇬🇧 English

**nettop** scans a network, finds the devices on it, works out their operating
systems and services, watches the traffic between them, and prints the result
in whatever shape you need: a terminal table, JSON, YAML, CSV, an ASCII
topology graph, ready-to-commit Markdown docs, or Prometheus metrics.

It is **CLI-first** on purpose. There is no web interface to run and no service
to babysit — just a single command that fits into scripts, cron jobs, CI
pipelines and monitoring stacks. It runs on the standard library alone, so a
plain `pip install` gives you a working tool with nothing else to set up. If
`nmap` and `tcpdump` happen to be installed, nettop uses them for richer OS
fingerprinting and traffic capture; if they are not, it falls back to its own
scanner and keeps going.

### Why

Most admins never have a complete picture of their own network — what is
connected, which ports are open, who talks to whom, how much traffic is moving.
The usual answers are either too low-level to give you the whole map (`nmap`,
`tcpdump` used one host at a time), too heavy to stand up for a quick look
(Zabbix, Nagios), or tied to a GUI you cannot use on a headless box
(Wireshark).

nettop fills the gap in the middle: run one command, get an understandable map
of the network in a format you can actually use. It works immediately, with no
configuration, and it is built for the terminal.

### Features

- **Device discovery** — ping sweep plus TCP probing finds live hosts, including
  ones that drop ICMP. No root required.
- **Port & service detection** — a curated port set with optional banner
  grabbing, mapped to friendly service names.
- **OS and vendor hints** — TTL-based OS family guess and MAC-vendor lookup out
  of the box; full fingerprinting when `nmap` is available.
- **Device classification** — servers, desktops, network gear, IoT and printers
  are told apart automatically.
- **Seven output formats** — `text`, `json`, `yaml`, `csv`, `ascii`,
  `markdown`, `prometheus`.
- **History & diffing** — every scan is stored in SQLite; `diff` shows exactly
  what changed between two of them.
- **Traffic analysis** — per-link bandwidth from a live `tcpdump` capture.
- **Daemon mode** — periodic scans, alerting, a REST API and a Prometheus
  `/metrics` endpoint, all on the standard library.
- **Honest error handling** — missing privileges, missing tools and unreachable
  networks produce a clear message, not a stack trace.

### Install

```bash
git clone https://github.com/Sliptval/network-topology-analyzer.git
cd network-topology-analyzer
pip install .
```

> **Recent Debian/Ubuntu:** if `pip install .` fails with
> `externally-managed-environment`, that's PEP 668 - the system Python
> deliberately refuses direct installs. Easiest fix: run
> `scripts/install.sh`, which detects this and installs nettop into a
> private venv automatically, no root needed. Manually, the equivalent is
> `pipx install .` or `python3 -m venv .venv && .venv/bin/pip install .`.

This puts a `nettop` command on your PATH. You can also run it straight from a
checkout without installing:

```bash
python -m nettop --help
# or
./nettop-cli --help
```

**Optional external tools.** nettop works with none of these, but collects
richer data when they are present:

| Tool      | Adds                                | Debian/Ubuntu         | macOS               |
| --------- | ----------------------------------- | --------------------- | ------------------- |
| `nmap`    | OS fingerprinting, service versions | `apt install nmap`    | `brew install nmap` |
| `tcpdump` | live traffic capture (`--traffic`)  | `apt install tcpdump` | preinstalled        |

Check your environment at any time: `nettop doctor`.

### Quick start

```bash
# Scan a subnet (auto-detects your local network if you omit --network)
nettop scan --network 192.168.1.0/24

# A deeper scan with banner/version detection, saved as JSON
nettop scan --network 192.168.1.0/24 --deep --output json --save scan.json

# Everything you know about one host
nettop device 192.168.1.5 --ports --services

# Draw the topology
nettop visualize

# Generate network documentation you can commit to a wiki
nettop export --format markdown --output network-docs.md
```

### Commands

| Command     | What it does                                                 |
| ----------- | ------------------------------------------------------------ |
| `scan`      | Discover devices, ports and services on a network.           |
| `device`    | Detailed information about a single host (with `--history`). |
| `monitor`   | Repeated scans on an interval, reporting changes.            |
| `diff`      | Compare two saved scans and list what changed.               |
| `export`    | Re-render the last stored scan in another format.            |
| `visualize` | ASCII topology graph of the last scan.                       |
| `trace`     | Trace the network route to a host.                           |
| `daemon`    | Background monitoring with alerts and an optional REST API.  |
| `doctor`    | Check the environment, privileges and optional tools.        |

Run `nettop <command> --help` for the full option list of any command.

`--network` accepts CIDR (`192.168.1.0/24`), a hyphen range
(`10.0.0.1-10.0.0.50`), a single IP, or a comma-separated mix. Omit it and
nettop uses the local network it detects.

### Output formats

Every format is available from `scan --output <fmt>` and from
`export --format <fmt>`.

<details>
<summary><strong>ASCII topology</strong> — <code>nettop visualize</code></summary>

```
192.168.1.0/24
└─ [gateway] 192.168.1.1
   ├─ db-server (192.168.1.5) [server]
   │  ├─ os: Linux/Unix
   │  └─ services: SSH, PostgreSQL, Redis
   ├─ web-server (192.168.1.6) [server]
   │  ├─ os: Linux/Unix
   │  └─ services: SSH, HTTP, HTTPS, Prometheus
   ├─ nas (192.168.1.10) [server]
   │  ├─ os: Linux/Unix
   │  └─ services: SSH, NetBIOS, SMB, UPnP/Flask
   └─ workstation (192.168.1.55) [desktop]
      ├─ os: Windows
      └─ services: MSRPC, NetBIOS, SMB, RDP
```
</details>

<details>
<summary><strong>Prometheus metrics</strong> — <code>--format prometheus</code></summary>

```
# HELP nettop_devices_online Devices currently online.
# TYPE nettop_devices_online gauge
nettop_devices_online{network="192.168.1.0/24"} 8
nettop_device_up{network="192.168.1.0/24",ip="192.168.1.5",hostname="db-server"} 1
nettop_device_open_ports{network="192.168.1.0/24",ip="192.168.1.5"} 3
nettop_bandwidth_mbps{source="192.168.1.6",dest="192.168.1.5",protocol="tcp"} 42.7
```
</details>

<details>
<summary><strong>JSON</strong> — <code>--output json</code></summary>

```json
{
  "scan_timestamp": "2026-05-18T09:14:02Z",
  "network": "192.168.1.0/24",
  "online_count": 8,
  "devices": [
    {
      "ip": "192.168.1.5",
      "hostname": "db-server",
      "os": "Linux/Unix",
      "status": "online",
      "ports": [22, 5432, 6379],
      "services": ["SSH", "PostgreSQL", "Redis"]
    }
  ]
}
```
</details>

The `docs/examples/home-lab.json` file in this repo is a full sample scan — try
the exporters on it without scanning anything:

```bash
nettop export --input docs/examples/home-lab.json --format markdown
nettop visualize --input docs/examples/home-lab.json
```

### Daemon mode & REST API

Run continuous monitoring with alerting and, optionally, a small HTTP API:

```bash
nettop daemon --config config/default.yaml
nettop daemon --network 192.168.1.0/24 --interval 5m --api 127.0.0.1:8080
```

The API is built on the standard library — no framework, no extra dependency:

| Endpoint                | Returns                           |
| ----------------------- | --------------------------------- |
| `GET /api/status`       | Daemon and last-scan summary      |
| `GET /api/devices`      | Every device from the latest scan |
| `GET /api/devices/<ip>` | One device                        |
| `GET /api/traffic`      | Observed connections              |
| `GET /api/alerts`       | Active alerts                     |
| `GET /metrics`          | Prometheus exposition             |

Alerts fire when a device goes offline, a new device appears, a link exceeds a
bandwidth threshold, or latency climbs past a limit — all configurable in the
YAML config ([`config/default.yaml`](config/default.yaml)). Install it as a
systemd service with `scripts/setup-daemon.sh`.

### How it works

```
nettop/
├── cli.py            Command parsing; turns errors into tidy messages
├── models.py         Device, Connection, Alert, ScanResult — the shared vocabulary
├── services.py       Port → service names and device-type heuristics
├── scanner/          Host discovery, port scanning, the optional nmap backend
├── traffic/          tcpdump capture and per-link bandwidth
├── storage/          SQLite history store
├── export/           One module per output format, behind a small registry
├── daemon/           Monitor loop, alert rules and the REST API
└── utils/            Address parsing, ARP/vendor lookup, privileges, logging
```

Each stage produces the same dataclasses, so the scanner, the database and the
exporters all speak the same language. Discovery and port scanning run in thread
pools; a `/24` typically completes in a few seconds even when most of it is
down.

### Requirements

- **Python 3.10 or newer.** No required third-party packages.
- Optional: `pyyaml` for prettier YAML; `nmap` for OS/version detection;
  `tcpdump` for traffic capture.
- Scanning works unprivileged. OS fingerprinting and traffic capture need
  root/Administrator; nettop checks and tells you when they do.

### Development

```bash
pip install -e ".[dev]"
pytest
```

### Responsible use

Only scan networks you own or are authorised to test. See
[docs/legal.md](docs/legal.md).

---

<div align="center">

Released under the [MIT License](LICENSE).

</div>
