# backend/ — бэкенд AI Sana Challenge Hub. Для агентов Арслана (Claude и Codex)

Сначала прочитай: `../AGENTS.md` (общий контекст, правила, зоны), `../docs/01-case.md` (кейс),
`../docs/02-api.md` (**замороженный контракт API**).

## Кто что делает

Бэкенд ведут два агента одновременно, в одной папке. Делим **по файлам**: чужие файлы не правим,
даже «чуть-чуть». Нужна правка в чужом файле — опиши, что нужно, Арслан передаст.

| Агент | Файлы | Задачи |
|---|---|---|
| **Claude** | `app/main.py`, `app/db.py`, `app/schema.sql`, `app/llm.py`, `app/errors.py`, `app/ai.py`, `app/tasks.py`, `tests/conftest.py`, `tests/test_{ai,tasks,scenario}.py`; `../run.sh`, `../.env.example`, `../docs/` (кроме `03-rating.md`), `../partner/` | контракт, ИИ-функции, жизненный цикл задачи, все роуты, запуск |
| **Codex** | `app/rating.py`, `app/catalog.py`, `app/proposals.py`, `tests/test_{rating,catalog,proposals}.py`; `../seed/*.json`, `../docs/03-rating.md`, `../README.md` | рейтинг, каталог, отклики и выбор бизнеса, синтетические данные, README |

## Соглашения

- Сигнатуры и докстринги — контракт между агентами: `main.py` и `tasks.py` вызывают функции
  модулей. Тело пиши под них; сигнатуру меняет только Claude.
- Функции модулей получают `conn` и **не делают `commit`** — транзакцию закрывает роут в `main.py`.
  Ошибки — `errors.NotFound / Conflict / BadRequest`, в HTTP их переводит `main.py`.
- Время наружу — ISO UTC с `Z` (`2026-09-23T08:40:00Z`).
- Тесты: фикстура `conn` из `tests/conftest.py` — БД в памяти со схемой и сидом; тесты не ходят
  в API (`DEMO_MODE=1`) и не трогают общую `hub.db`.
- Агенты не коммитят: коммиты и push делает Арслан.

## Команды (из `backend/`)

```bash
../.venv/bin/python -m pytest                       # тесты
../.venv/bin/python -m app.db                       # пересоздать БД и сид
../.venv/bin/uvicorn app.main:app --reload --port 8000   # http://localhost:8000/api/health
```
Окружение с нуля — `../run.sh` или ручные шаги из `../README.md`.
