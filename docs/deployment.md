# Deployment Guide

This quick guide focuses on **local**, **CI**, and **cloud** (Heroku-like) setups.

## 1. Local

```bash
python -m venv .venv && . .venv/Scripts/activate  # Windows
pip install -r requirements.txt
python main.py  # runs example pipeline + strategy
```

## 2. Continuous Integration (GitHub Actions)

CI workflow already lives at `.github/workflows/ci.yml` and runs:

* `pip install -r requirements.txt`
* `pytest --cov` – full test suite

Coverage report is uploaded as an artifact.

## 3. Docker (Optional)

```dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY . .
RUN pip install -r requirements.txt
CMD ["python", "main.py"]
```

Build & run:

```bash
docker build -t missile .
docker run -e SETTINGS_PATH=/app/config/settings.yaml missile
```

## 4. Cloud Database

Set the `DATABASE_URL` env var (e.g., Supabase, Neon) and MagicMissile will auto-migrate on start.

## 5. Live Trading Tips

1. Start with `PaperBroker` → no real cash at risk.
2. Gradually switch to live keys in `config/brokers.yaml`.
3. Run the engine in `tmux`/`screen` or containerised service.

_Last updated: 2025-06-26._
