# NSE Swing Trading Agent — Full-Stack App

Institutional-grade autonomous trading dashboard built with **Django + Celery + React**.

## Quick Start

### Prerequisites
- Python 3.10+
- Node.js 18+
- Redis (for Celery + Channels)

### 1. Start Redis
**Using WSL2 (recommended on Windows):**
```bash
wsl redis-server
```
Or install [Redis for Windows](https://github.com/microsoftarchive/redis/releases) and run `redis-server`.

### 2. Backend Setup
```bash
cd backend
pip install -r requirements.txt

# Apply migrations
python manage.py migrate

# Create admin user (optional)
python manage.py createsuperuser

# Start Django (ASGI via Daphne)
daphne -p 8000 config.asgi:application
```

### 3. Start Celery Worker (new terminal)
```bash
cd backend
celery -A config worker -l info -P solo
```
> `-P solo` is recommended for Windows (no fork support).

### 4. Frontend Setup
```bash
cd frontend
npm install
npm run dev
```
App opens at **http://localhost:5173**. API is proxied to Django on port 8000.

---

## Architecture

```
frontend/          React + Vite + Tailwind (port 5173)
backend/
  config/          Django settings, ASGI, Celery, URLs
  apps/
    signals/       ML prediction pipeline (predict.py → DB)
    research/      Two-tier LLM agent (agent.py → DB)
    execution/     Dhan Sandbox order execution
    portfolio/     Paper position tracker (TP/SL/expiry)
    model_mgmt/    LightGBM retrain
    ws/            WebSocket consumers (task logs + live PnL)
  core/            Shared utilities
```

## Key Pages

| Route | Description |
|---|---|
| `/` | Dashboard — KPIs, equity curve, recent activity |
| `/signals` | ML signals table, trigger prediction |
| `/audit` | AI Audit dossier — expandable cards |
| `/portfolio` | Open positions + closed trades with multi-broker P&L |
| `/orders` | Order history + live Dhan sandbox refresh |
| `/execute` | Select & fire trades to Dhan Sandbox |
| `/model` | Retrain LightGBM, view metrics & feature importances |
| `/settings` | API keys reference, trading params, fee profiles |

## Fee Simulation
Every closed trade shows P&L under 4 broker profiles:
- **Zerodha** — ₹20 flat or 0.03% (lower) + full statutory
- **Dhan** — same as Zerodha
- **Groww** — ₹20 flat + full statutory  
- **Angel One** — ₹20 flat + full statutory

Statutory charges modelled: STT (0.1%), NSE exchange (0.00335%), GST (18%), SEBI (₹10/Cr), Stamp duty (0.015%).
