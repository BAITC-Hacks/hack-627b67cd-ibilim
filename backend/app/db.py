"""SQLite: подключение, схема, сид демо-данных."""

import json
import os
import sqlite3
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DB_PATH = Path(os.getenv("DB_PATH", ROOT / "backend" / "ibilim.db"))
SCHEMA = Path(__file__).with_name("schema.sql")
SEED_OBJECTIVES = ROOT / "seed" / "objectives.7.algebra.json"


def connect() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init() -> None:
    conn = connect()
    conn.executescript(SCHEMA.read_text(encoding="utf-8"))
    conn.commit()
    if conn.execute("SELECT COUNT(*) AS n FROM objective").fetchone()["n"] == 0:
        seed(conn)
    conn.close()


def seed(conn: sqlite3.Connection) -> None:
    """Демо-класс 7А: 12 учеников тремя профилями, чтобы персональная домашка была видимо разной."""
    data = json.loads(SEED_OBJECTIVES.read_text(encoding="utf-8"))
    for obj in data["objectives"]:
        conn.execute(
            """INSERT OR REPLACE INTO objective
               (code, grade, subject, section, subsection, quarter, hours, order_index,
                text_ru, text_kk, prerequisites, source)
               VALUES (?,?,?,?,?,?,?,?,?,?,?,?)""",
            (
                obj["code"], data["grade"], data["subject"], obj.get("section"),
                obj.get("subsection"), obj.get("quarter"), obj.get("hours", 0),
                obj.get("order_index", 0), obj["text_ru"], obj.get("text_kk", ""),
                json.dumps(obj.get("prerequisites", []), ensure_ascii=False),
                obj.get("source", "DRAFT"),
            ),
        )

    conn.execute(
        "INSERT OR REPLACE INTO klass (id, name, grade, subject, language) VALUES (1, '7А', 7, 'Алгебра', 'ru')"
    )
    conn.execute(
        "INSERT OR REPLACE INTO calendar (id, quarter, starts_on, ends_on, holidays)"
        " VALUES (1, 1, '2026-09-01', '2026-10-25', '[]')"
    )
    for weekday, lesson_no in ((1, 3), (3, 2), (5, 4)):
        conn.execute(
            "INSERT INTO schedule_slot (klass_id, weekday, lesson_no) VALUES (1, ?, ?)",
            (weekday, lesson_no),
        )

    # профили: strong / medium / weak — weak проваливает 7.2.1.4, это главный кадр демо
    roster = [
        ("Айдар", "weak"), ("Дана", "weak"), ("Алишер", "medium"), ("Камила", "medium"),
        ("Ержан", "medium"), ("Аружан", "strong"), ("Тимур", "strong"), ("Мадина", "medium"),
        ("Санжар", "weak"), ("Айсулу", "medium"), ("Нурлан", "strong"), ("Жанель", "medium"),
    ]
    levels = {"strong": 0.88, "medium": 0.62, "weak": 0.28}
    codes = [row["code"] for row in conn.execute(
        "SELECT code FROM objective WHERE quarter = 1 ORDER BY order_index"
    )]
    for name, profile in roster:
        cur = conn.execute("INSERT INTO student (klass_id, name) VALUES (1, ?)", (name,))
        student_id = cur.lastrowid
        for code in codes[:3]:  # уже пройденные цели раздела
            value = levels[profile]
            if profile == "weak" and code == "7.2.1.3":
                value = 0.20
            conn.execute(
                "INSERT OR REPLACE INTO mastery (student_id, objective_code, value, attempts)"
                " VALUES (?,?,?,?)",
                (student_id, code, value, 3),
            )
    conn.commit()


if __name__ == "__main__":
    init()
    print(f"db ready: {DB_PATH}")
