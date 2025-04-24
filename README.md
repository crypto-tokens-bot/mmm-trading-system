# MMM Trading System – Installation & Quick Start Guide

**MMM Trading System** is an algorithmic‑trading bot with a backtesting system.

## 1. System & Software Requirements

### Hardware Sizing

| Resource | **Minimum**         | **Recommended** (multi‑market) |
|----------|---------------------|-------------------------------|
| CPU      | 2   vCPUs             | 4–8   vCPUs                   |
| RAM      | 2   GiB               | 16   GiB or more              |
| Disk     | 2   GiB SSD           | 100   GiB+ fast SSD           |
| Network  | 5 Mbps ↓ / 1   Mbps ↑ | 500   Mbps sym.               |

### Supported Operating Systems

* **Ubuntu** 22.04 LTS or newer
* **macOS** 14 (Sonoma) or newer
* **Windows 11** (native Docker Desktop)

### Software Stack

| Tool | **Minimum version** | **Recommended** |
|------|---------------------|-----------------|
| Docker | 23.x | latest stable |
| Docker Compose | 2.x | latest |
| Git | 2.x | latest |
| *(optional)* Python | 3.12 | latest 3.12.x |
| *(optional)* GNU Make | 4.x | latest |

> If you launch **only** via Docker Compose you can skip installing Python and Make on the host.

---

## 2. Clone the repository

```bash
git clone https://github.com/crypto-tokens-bot/mmm-trading-system.git
cd mmm-trading-system
```

---

## 3. Environment variables (`.env`)

Create a `.env` file in the **project root** and define the variables below.

| Variable | Required | Description |
|----------|----------|-------------|
| `BYBIT_API_KEY` | yes | **Live** Bybit API key (real trading) |
| `BYBIT_API_SECRET` | yes | Secret that matches `BYBIT_API_KEY` |
| `BYBIT_API_KEY_TESTNET` | no | **Testnet** key (paper trading) |
| `BYBIT_API_SECRET_TESTNET` | no | Secret for Bybit testnet |
| `CLICKHOUSE_USER` | yes | ClickHouse user (*default*: `default`) |
| `CLICKHOUSE_PASSWORD` | yes | Password for the above user |
| `LOKI_URL` | yes | Endpoint for pushing logs <`http://loki:3100/loki/api/v1/push`> |
| `GRAFANA_API_KEY` | yes | Admin‑level key used to render panels / import dashboards |
| `GRAFANA_USER` | no | Grafana username when not using `GRAFANA_API_KEY` |
| `GRAFANA_PASSWORD` | no | Password for `GRAFANA_USER` |
| `TELEGRAM_TOKEN` | yes | Token of the Telegram bot sending alerts |
| `ADMINS` | yes | Comma‑separated Telegram user IDs with admin rights |

---

## 4. Spin up the infrastructure (Docker Compose)

`docker-compose.yml` already includes ClickHouse, Loki, Grafana and the image renderer. Run:

```bash
docker compose up -d   # pull images & start in the background
```

Check that all services are healthy:

```bash
docker compose ps
```

---

## 5. Apply database migrations

After ClickHouse is up, execute:

```bash
python -m src.manage init
```

The command scans `src/db/migrations/*.sql` and executes them sequentially.

---

## 6. Start the bot

### 6.1 In a container (recommended)

Add a service called `app` to `docker-compose.yml` (if it is not there yet) and run:

```bash
docker compose up -d --build app
```

Tail logs:

```bash
docker compose logs -f app
```

### 6.2 Locally from source

```bash
python -m venv venv
source venv/bin/activate          # Windows: .\venv\Scripts\activate
pip install --upgrade pip
pip install -r requirements.txt

python src/main.py
```

Stop with **Ctrl   +C**.

---

## 7. Built‑in CLI commands

`src/manage.py` is a **Click**‑based interface for quick maintenance. Examples:

| Command | Action |
|---------|--------|
| `python -m src.manage init` | run migrations |
| `python -m src.manage list_event_managers` | list event managers |
| `python -m src.manage create_event_manager --name "MM Bot"` | add an event manager |
| `python -m src.manage remove_event_manager --id <uuid>` | delete an event manager |
| `python -m src.manage list_strategies` | list strategies |
| `python -m src.manage create_strategy --json ./strategy.json` | add strategy from JSON |
| `python -m src.manage list_portfolios` | list portfolios |
| `python -m src.manage list_subscriptions` | list portfolio↔strategy links |

All commands are also available as Make targets in `cli.mk`.

---

## 8. Importing the Grafana dashboard

A dashboard definition is located in `grafana/dashboard.json` and can be imported via the Grafana UI.

1. Log in to Grafana (<http://localhost:3000>, user/pass from `.env` or defaults).
2. **Create   → Import   Dashboard**.
3. Upload `grafana/dashboard.json` and choose the Loki / ClickHouse data sources.

---

Everything is ready! With `.env` set and containers running the bot will start trading and streaming logs to Loki   →   Grafana. Manage reference data via the CLI and re‑run `init` whenever you add new SQL migrations.
