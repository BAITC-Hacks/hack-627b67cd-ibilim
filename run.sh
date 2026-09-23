#!/usr/bin/env bash
# Запуск одной командой: ./run.sh → http://localhost:8000
# macOS / Linux. Нужен Python 3.11–3.14; для веба — Node 18+ (без него поднимется только API).
set -euo pipefail
cd "$(dirname "$0")"

PY=""
for candidate in python3.12 python3.13 python3.11 python3.14 python3; do
  if command -v "$candidate" >/dev/null 2>&1 &&
     "$candidate" -c 'import sys; sys.exit(0 if (3, 11) <= sys.version_info[:2] <= (3, 14) else 1)'; then
    PY="$candidate"; break
  fi
done
[ -n "$PY" ] || { echo "Нужен Python 3.11–3.14"; exit 1; }

[ -d .venv ] || "$PY" -m venv .venv
.venv/bin/pip install -q -r backend/requirements.txt
[ -f .env ] || cp .env.example .env   # без OPENAI_API_KEY работает локальная заглушка ИИ

if [ -f web/package.json ] && command -v npm >/dev/null 2>&1; then
  (cd web && npm install --no-audit --no-fund && npm run build)
fi

cd backend
../.venv/bin/python -m app.db                      # чистая БД с синтетическими данными
exec ../.venv/bin/uvicorn app.main:app --host 0.0.0.0 --port "${PORT:-8000}"
