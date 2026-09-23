"""SQLite: подключение, схема, синтетические данные из seed/*.json (ТЗ §6)."""

import json
import os
import sqlite3
from pathlib import Path

from . import rating

ROOT = Path(__file__).resolve().parents[2]
DB_PATH = Path(os.getenv("DB_PATH", "ibilim.db"))
if not DB_PATH.is_absolute():  # относительный путь — от backend/, а не от папки запуска
    DB_PATH = ROOT / "backend" / DB_PATH
SCHEMA = Path(__file__).with_name("schema.sql")
SEED = ROOT / "seed"


def connect() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init() -> None:
    conn = connect()
    conn.executescript(SCHEMA.read_text(encoding="utf-8"))
    conn.commit()
    if conn.execute("SELECT COUNT(*) AS n FROM business").fetchone()["n"] == 0:
        seed(conn)
    conn.close()


def load(name: str) -> list[dict]:
    """seed/<name>.json → список; нет файла — пустой список."""
    path = SEED / f"{name}.json"
    return json.loads(path.read_text(encoding="utf-8")) if path.exists() else []


def _json(value) -> str:
    return json.dumps(value, ensure_ascii=False)


def seed(conn: sqlite3.Connection) -> None:
    """Бизнесы, команды, опубликованные карточки и отклики. Официальный рейтинг карточек
    считает rating.score — тот же код, что и в работе, чтобы каталог не расходился с формулой."""
    for b in load("businesses"):
        conn.execute(
            "INSERT INTO business (id, name, industry, contact) VALUES (?,?,?,?)",
            (b["id"], b["name"], b.get("industry"), b.get("contact")),
        )
    for t in load("teams"):
        conn.execute(
            "INSERT INTO team (id, name, interests, skills, technologies) VALUES (?,?,?,?,?)",
            (t["id"], t["name"], _json(t.get("interests", [])), _json(t.get("skills", [])),
             _json(t.get("technologies", []))),
        )
    for c in load("cards"):
        card = {field: c["card"].get(field, "") for field in rating.FIELDS}
        try:
            r = rating.score(card)
            score, level = r["score"], r["level"]
        except NotImplementedError:  # рейтинг ещё не написан — карточка без балла
            score, level = None, None
        conn.execute(
            """INSERT INTO task (id, business_id, industry, draft_text, status, card, sources,
                                 confirmed, confirmed_card, score, level, published_at)
               VALUES (?,?,?,?, 'published', ?,?, 1, ?,?,?, datetime('now', ?))""",
            (c["id"], c["business_id"], c.get("industry"), c.get("draft_text", ""), _json(card),
             _json({f: "manual" for f, v in card.items() if v}), _json(card), score, level,
             f"-{c['id']} hours"),
        )
        if score is not None:
            conn.execute(
                "INSERT INTO rating_event (task_id, event, score, level, confirmed) VALUES (?, 'confirm', ?, ?, 1)",
                (c["id"], score, level),
            )
    for p in load("proposals"):
        conn.execute(
            """INSERT INTO proposal (task_id, team_id, idea, plan, timeline, link, status)
               VALUES (?,?,?,?,?,?,?)""",
            (p["task_id"], p["team_id"], p["idea"], p["plan"], p["timeline"], p["link"],
             p.get("status", "submitted")),
        )
    conn.commit()


if __name__ == "__main__":
    for suffix in ("", "-wal", "-shm"):
        Path(f"{DB_PATH}{suffix}").unlink(missing_ok=True)
    init()
    print(f"db recreated: {DB_PATH}")
