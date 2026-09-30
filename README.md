# CipherGate

Secure API Authentication System

## Local Setup

1. Backend:
```bash
python -m venv .venv
source .venv/bin/activate
pip install -r backend/requirements.txt
python backend/scripts/generate_keys.py
cp .env.example .env
alembic upgrade head
uvicorn app.main:app --host 127.0.0.1 --port 8000
```

2. Frontend:
```bash
npm ci
npm run dev
```
