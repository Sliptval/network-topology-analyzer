<h1 align="center">nettop</h1>

<p align="center">
  <strong>Понятная карта твоей сети — одной командой, прямо в терминале.</strong>
</p>

<p align="center">
  <a href="#установка">Установка</a> ·
  <a href="#быстрый-старт">Быстрый старт</a> ·
  <a href="#команды">Команды</a> ·
  <a href="#форматы-вывода">Форматы вывода</a> ·
  <a href="#режим-демона-и-rest-api">Демон и API</a>
</p>

<p align="center">
  <img src="https://img.shields.io/badge/python-3.10+-3776AB.svg?logo=python&logoColor=white" alt="Python 3.10+">
  <img src="https://img.shields.io/badge/license-MIT-green.svg" alt="MIT License">
  <img src="https://img.shields.io/badge/platform-linux%20%7C%20macos%20%7C%20windows-lightgrey.svg" alt="Кроссплатформенно">
  <img src="https://img.shields.io/badge/dependencies-stdlib%20only-brightgreen.svg" alt="Только стандартная библиотека">
</p>

<p align="center">
  <a href="README.md">English</a> · <a href="README.ru.md">Русский</a>
</p>

---

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

Summary
  Devices by type:
    server     4
    desktop    1
    iot        1
    network    1
    printer    1
```

## Зачем это нужно

У большинства администраторов нет полной картины собственной сети: что
подключено, какие порты открыты, кто с кем общается, сколько идёт трафика.
Привычные ответы — либо слишком низкоуровневые, чтобы собрать из них карту
(`nmap`, `tcpdump` по одному хосту), либо слишком тяжёлые, чтобы разворачивать
их ради быстрого взгляда (Zabbix, Nagios), либо завязаны на графический
интерфейс, которого нет на headless-сервере (Wireshark).

nettop закрывает нишу посередине: запустил одну команду — получил понятную карту
сети в формате, с которым реально можно работать. Работает сразу, без
настройки, и сделан для терминала.

## Возможности

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

## Установка

### Из исходников

```bash
git clone https://github.com/Sliptval/network-topology-analyzer.git
cd network-topology-analyzer
pip install .
```

После этого команда `nettop` доступна в PATH. Можно запускать и прямо из
каталога, без установки:

```bash
python -m nettop --help
# или
./nettop-cli --help
```

### Опциональные внешние утилиты

nettop работает и без них, но с ними собирает более точные данные:

| Утилита   | Что добавляет                          | Debian/Ubuntu            | macOS               |
| --------- | -------------------------------------- | ------------------------ | ------------------- |
| `nmap`    | fingerprint ОС, версии сервисов        | `apt install nmap`       | `brew install nmap` |
| `tcpdump` | захват живого трафика (`--traffic`)     | `apt install tcpdump`    | предустановлен      |

Проверить окружение можно в любой момент:

```bash
nettop doctor
```

## Быстрый старт

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

## Команды

| Команда      | Что делает                                                          |
| ------------ | ------------------------------------------------------------------- |
| `scan`       | Обнаружить устройства, порты и сервисы в сети.                       |
| `device`     | Подробная информация об одном хосте (в т.ч. `--history`).            |
| `monitor`    | Повторяющиеся сканы с интервалом; сообщает об изменениях.            |
| `diff`       | Сравнить два сохранённых скана и показать изменения.                 |
| `export`     | Перерисовать последний скан в другом формате.                        |
| `visualize`  | ASCII-граф топологии последнего скана.                              |
| `trace`      | Трассировка маршрута до хоста.                                       |
| `daemon`     | Фоновый мониторинг с алертами и опциональным REST API.              |
| `doctor`     | Проверить окружение, права и опциональные утилиты.                   |

Полный список опций любой команды — `nettop <команда> --help`.

### scan

```bash
nettop scan --network 192.168.1.0/24            # таблица (по умолчанию)
nettop scan --network 192.168.1.0/24 --ports --deep
nettop scan --network 10.0.0.1-10.0.0.50 --output json
nettop scan --network 192.168.1.0/24 --traffic --duration 30s
```

`--network` принимает CIDR (`192.168.1.0/24`), диапазон через дефис
(`10.0.0.1-10.0.0.50`), одиночный IP или их сочетание через запятую. Если его не
указать, nettop возьмёт определённую им локальную сеть.

### device

```bash
nettop device 192.168.1.5                  # последние данные из истории
nettop device 192.168.1.5 --ports          # опросить прямо сейчас
nettop device 192.168.1.5 --history        # все прошлые появления
```

### diff

```bash
nettop diff scan-monday.json scan-friday.json
```

```
Topology changes

New devices (1):
  + 192.168.1.42  laptop

Port changes:
  192.168.1.5  opened: 6379
```

## Форматы вывода

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
<summary><strong>Markdown-документация</strong> — <code>--format markdown</code></summary>

```markdown
# Network Documentation — `192.168.1.0/24`

_Generated 2026-05-18T09:14:02Z · 8 device(s), 8 online._

## Devices

| IP | Hostname | Type | OS | Open ports |
| --- | --- | --- | --- | --- |
| `192.168.1.1` | router | network | Network device | 53, 80, 443 |
| `192.168.1.5` | db-server | server | Linux/Unix | 22, 5432, 6379 |
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

## Режим демона и REST API

Непрерывный мониторинг с алертами и, при желании, небольшим HTTP API:

```bash
nettop daemon --config config/default.yaml
nettop daemon --network 192.168.1.0/24 --interval 5m --api 127.0.0.1:8080
```

API построен на стандартной библиотеке — без фреймворка и лишних зависимостей:

| Эндпоинт                | Отдаёт                                     |
| ----------------------- | ------------------------------------------ |
| `GET /api/status`       | Сводку по демону и последнему скану        |
| `GET /api/devices`      | Все устройства из последнего скана         |
| `GET /api/devices/<ip>` | Одно устройство                            |
| `GET /api/traffic`      | Наблюдаемые соединения                     |
| `GET /api/alerts`       | Активные алерты                            |
| `GET /metrics`          | Метрики в формате Prometheus               |

Алерты срабатывают, когда устройство ушло в офлайн, появилось новое устройство,
соединение превысило порог по bandwidth или задержка выросла выше лимита — всё
это настраивается в YAML-конфиге.

### Prometheus и Grafana

Направь Prometheus на демон:

```yaml
scrape_configs:
  - job_name: nettop
    static_configs:
      - targets: ["127.0.0.1:8080"]
```

Дальше строй графики по `nettop_devices_online`, `nettop_device_up` или
`nettop_bandwidth_mbps` в Grafana.

### Запуск как сервис

```bash
sudo scripts/setup-daemon.sh /etc/nettop/config.yaml
systemctl status nettop
journalctl -u nettop -f
```

## Конфигурация

Конфиг необязателен — у каждой настройки есть значение по умолчанию, и её можно
передать флагом. Он нужен в первую очередь для того, чтобы демону не приходилось
передавать десяток аргументов. Полный пример с комментариями —
[`config/default.yaml`](config/default.yaml).

```yaml
network: 192.168.1.0/24
scan_interval: 5m
alerts:
  offline: true
  new_device: true
  high_bandwidth_mbps: 500
  slow_latency_ms: 200
api:
  enabled: true
  bind: 127.0.0.1:8080
```

## Как это устроено

```
nettop/
├── cli.py            Разбор команд и диспетчеризация; превращает ошибки в понятные сообщения
├── models.py         Device, Connection, Alert, ScanResult — общий словарь данных
├── services.py       Порт → имя сервиса и эвристики типа устройства
├── scanner/          Обнаружение хостов, сканирование портов, опциональный бэкенд nmap
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

## Требования

- **Python 3.10 или новее.** Обязательных сторонних пакетов нет.
- Опционально: `pyyaml` для более аккуратного YAML-вывода и YAML-конфигов
  (иначе работает встроенный fallback).
- Опционально: `nmap` для определения ОС/версий, `tcpdump` для захвата трафика.
- Сканирование работает без прав root. Fingerprint ОС и захват трафика требуют
  root/Администратора; nettop проверяет это и сообщает, когда прав не хватает.

## Разработка

```bash
pip install -e ".[dev]"
pytest
```

Юнит-тесты покрывают работу с адресами, все экспортёры, движок diff, правила
алертов, классификацию и хранилище.

## Ответственное использование

Сканируй только те сети, которыми владеешь или на тестирование которых у тебя
есть разрешение. Сканирование портов и захват пакетов в чужих сетях могут
нарушать правила — или закон. Подробнее — [docs/legal.md](docs/legal.md).

## Лицензия

Распространяется под [лицензией MIT](LICENSE).
