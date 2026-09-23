"""Жизненный цикл задачи: черновик → вопросы → карточка → подтверждение → публикация.

Владелец — Claude. Склеивает ai (вопросы, карточка) и rating (баллы); формат — объект Task
в docs/02-api.md. Функции не делают commit: транзакцию закрывает роут в main.py.
"""

import json
import sqlite3

from . import ai, catalog, db, privacy, rating
from .errors import BadRequest, Conflict, NotFound

INDUSTRIES = ["Агро", "Ритейл", "Логистика", "Образование", "Финансы", "Производство", "IT", "Госсектор"]
MAX_DRAFT, MAX_FIELD = 5000, 2000
RECOMMENDABLE = {"working", "ready", "priority"}  # ТЗ §4: рекомендовать можно с «рабочей»


def meta() -> dict:
    levels = sorted(rating.LEVELS)  # по возрастанию нижней границы
    return {
        "industries": INDUSTRIES,
        "fields": [{"key": f, "label": ai.LABELS[f]} for f in rating.FIELDS],
        "indicators": [
            {"key": key, "label": label, "max": weight, "fields": list(fields)}
            for key, label, weight, fields in rating.INDICATORS
        ],
        "levels": [
            {"key": key, "label": label, "min": low,
             "max": levels[i + 1][0] - 1 if i + 1 < len(levels) else 100}
            for i, (low, key, label) in enumerate(levels)
        ],
        "draft_examples": db.load("drafts"),
    }


def _iso(value: str | None) -> str | None:
    return value.replace(" ", "T") + "Z" if value else None  # SQLite хранит UTC


def _blank_card() -> dict:
    return {f: "" for f in rating.FIELDS}


def _row(conn: sqlite3.Connection, task_id: int) -> sqlite3.Row:
    row = conn.execute("SELECT * FROM task WHERE id = ?", (task_id,)).fetchone()
    if row is None:
        raise NotFound("задача не найдена")
    return row


def _log(conn: sqlite3.Connection, task_id: int, event: str, card: dict, confirmed: bool) -> dict:
    r = rating.score(card)
    last = conn.execute(
        "SELECT event, score FROM rating_event WHERE task_id = ? ORDER BY id DESC LIMIT 1", (task_id,)
    ).fetchone()
    # правки без изменения балла ленту не засоряют
    if not (event == "edit" and last and last["score"] == r["score"]):
        conn.execute(
            "INSERT INTO rating_event (task_id, event, score, level, confirmed) VALUES (?,?,?,?,?)",
            (task_id, event, r["score"], r["level"], int(confirmed)),
        )
    return r


def _out(conn: sqlite3.Connection, row: sqlite3.Row) -> dict:
    card = {**_blank_card(), **json.loads(row["card"])}
    business = conn.execute("SELECT id, name FROM business WHERE id = ?", (row["business_id"],)).fetchone()
    questions = conn.execute(
        "SELECT id, field, text, answer FROM question WHERE task_id = ? ORDER BY id", (row["id"],)
    ).fetchall()
    history = conn.execute(
        "SELECT created_at, event, score, level, confirmed FROM rating_event WHERE task_id = ? ORDER BY id",
        (row["id"],),
    ).fetchall()
    proposals = conn.execute("SELECT COUNT(*) AS n FROM proposal WHERE task_id = ?", (row["id"],)).fetchone()["n"]
    preview = rating.score(card)
    # опубликованная стоит по официальному баллу, неопубликованная — прогноз по текущему
    published = row["status"] == "published" and row["score"] is not None
    position = {**catalog.place(conn, row["score"] if published else preview["score"], row["id"]),
                "projected": not published}
    teams = catalog.audience(conn, row["industry"] or "", card)
    level_now = row["level"] if published else preview["level"]
    # «что даст улучшение»: балл, место и кому начнут рекомендовать, если довести показатель до максимума
    for item in preview["next_best"]:
        then_score = min(100, preview["score"] + item["gain"])
        then_level, _ = rating.level(then_score)
        item["then"] = {
            "score": then_score, "level": then_level, **catalog.place(conn, then_score, row["id"]),
            "teams": [t["name"] for t in teams] if then_level in RECOMMENDABLE else [],
        }
    return {
        "id": row["id"],
        "status": row["status"],
        "business": {"id": business["id"], "name": business["name"]},
        "industry": row["industry"] or "",
        "draft_text": row["draft_text"],
        "card": card,
        "sources": json.loads(row["sources"]),
        "questions": [dict(q) for q in questions],
        "rating": preview,
        "confirmed": bool(row["confirmed"]),
        "official": {"score": row["score"], "level": row["level"]} if row["score"] is not None else None,
        "position": position,
        "audience": {"recommended": level_now in RECOMMENDABLE, "teams": teams},
        # контакт и формат — данные самого бизнеса, их не проверяем
        "privacy": json.loads(row["privacy"]) + privacy.warnings({
            "draft": row["draft_text"],
            **{f: v for f, v in card.items() if v and f not in ("contact", "interaction_format")},
        }),
        "history": [
            {"at": _iso(h["created_at"]), "event": h["event"], "score": h["score"],
             "level": h["level"], "confirmed": bool(h["confirmed"])}
            for h in history
        ],
        "ai": json.loads(row["ai_meta"]),
        "proposals": proposals,
        "published_at": _iso(row["published_at"]),
    }


def create(conn: sqlite3.Connection, business_id: int, draft_text: str, industry: str) -> dict:
    draft_text = draft_text.strip()
    if not draft_text:
        raise BadRequest("черновик пустой — опишите задачу хотя бы одной фразой")
    if len(draft_text) > MAX_DRAFT:
        raise BadRequest(f"черновик длиннее {MAX_DRAFT} символов")
    business = conn.execute("SELECT industry FROM business WHERE id = ?", (business_id,)).fetchone()
    if business is None:
        raise NotFound("бизнес не найден")
    industry = industry.strip() or (business["industry"] or "")

    draft_text, masked = privacy.mask(draft_text, "draft")  # до ИИ и до записи в БД
    result = ai.analyze_draft(draft_text, industry)
    card = {**_blank_card(), **result["card"]}
    cur = conn.execute(
        "INSERT INTO task (business_id, industry, draft_text, status, card, sources, ai_meta, privacy)"
        " VALUES (?,?,?, 'new', ?,?,?,?)",
        (business_id, industry, draft_text, json.dumps(card, ensure_ascii=False),
         json.dumps(result["sources"], ensure_ascii=False), json.dumps(result["ai"], ensure_ascii=False),
         json.dumps(masked, ensure_ascii=False)),
    )
    task_id = cur.lastrowid
    conn.executemany(
        "INSERT INTO question (task_id, field, text) VALUES (?,?,?)",
        [(task_id, q["field"], q["text"]) for q in result["questions"]],
    )
    _log(conn, task_id, "draft", card, confirmed=False)
    return _out(conn, _row(conn, task_id))


def get(conn: sqlite3.Connection, task_id: int) -> dict:
    return _out(conn, _row(conn, task_id))


def for_business(conn: sqlite3.Connection, business_id: int) -> list[dict]:
    if conn.execute("SELECT 1 FROM business WHERE id = ?", (business_id,)).fetchone() is None:
        raise NotFound("бизнес не найден")
    rows = conn.execute("SELECT * FROM task WHERE business_id = ? ORDER BY id DESC", (business_id,)).fetchall()
    return [_out(conn, r) for r in rows]


def answer(conn: sqlite3.Connection, task_id: int, answers: list[dict]) -> dict:
    row = _row(conn, task_id)
    own = {q["id"]: q["field"] for q in conn.execute("SELECT id, field FROM question WHERE task_id = ?", (task_id,))}
    masked = json.loads(row["privacy"])
    for a in answers:
        if a["question_id"] not in own:
            raise BadRequest(f"вопрос {a['question_id']} не относится к задаче {task_id}")
        text, found = privacy.mask((a.get("answer") or "").strip()[:MAX_FIELD], own[a["question_id"]])
        masked = privacy.merge(masked, found)
        conn.execute("UPDATE question SET answer = ? WHERE id = ?", (text or None, a["question_id"]))
    conn.execute("UPDATE task SET privacy = ? WHERE id = ?", (json.dumps(masked, ensure_ascii=False), task_id))

    qa = [dict(q) for q in conn.execute("SELECT field, text, answer FROM question WHERE task_id = ? ORDER BY id", (task_id,))]
    card = {**_blank_card(), **json.loads(row["card"])}
    result = ai.build_card(row["draft_text"], qa, card, json.loads(row["sources"]))
    conn.execute(
        "UPDATE task SET card = ?, sources = ?, ai_meta = ?, confirmed = 0,"
        " status = CASE status WHEN 'new' THEN 'card' ELSE status END WHERE id = ?",
        (json.dumps(result["card"], ensure_ascii=False), json.dumps(result["sources"], ensure_ascii=False),
         json.dumps(result["ai"], ensure_ascii=False), task_id),
    )
    _log(conn, task_id, "answers", result["card"], confirmed=False)
    return _out(conn, _row(conn, task_id))


def edit(conn: sqlite3.Connection, task_id: int, patch: dict) -> dict:
    row = _row(conn, task_id)
    unknown = set(patch) - set(rating.FIELDS)
    if unknown:
        raise BadRequest(f"неизвестные поля карточки: {', '.join(sorted(unknown))}")
    card = {**_blank_card(), **json.loads(row["card"])}
    sources = json.loads(row["sources"])
    masked = json.loads(row["privacy"])
    for field, value in patch.items():
        if len(value.strip()) > MAX_FIELD:
            raise BadRequest(f"поле {ai.LABELS[field]} длиннее {MAX_FIELD} символов")
        value, found = privacy.mask(value.strip(), field)
        masked = privacy.merge(masked, found)
        if value == card[field]:
            continue
        card[field] = value
        if value:
            sources[field] = "manual"
        else:
            sources.pop(field, None)
    conn.execute(
        "UPDATE task SET card = ?, sources = ?, privacy = ?, confirmed = 0,"
        " status = CASE status WHEN 'new' THEN 'card' ELSE status END WHERE id = ?",
        (json.dumps(card, ensure_ascii=False), json.dumps(sources, ensure_ascii=False),
         json.dumps(masked, ensure_ascii=False), task_id),
    )
    _log(conn, task_id, "edit", card, confirmed=False)
    return _out(conn, _row(conn, task_id))


def confirm(conn: sqlite3.Connection, task_id: int) -> dict:
    row = _row(conn, task_id)
    card = {**_blank_card(), **json.loads(row["card"])}
    r = _log(conn, task_id, "confirm", card, confirmed=True)
    conn.execute(
        "UPDATE task SET confirmed = 1, confirmed_card = ?, score = ?, level = ?,"
        " status = CASE status WHEN 'new' THEN 'card' ELSE status END WHERE id = ?",
        (json.dumps(card, ensure_ascii=False), r["score"], r["level"], task_id),
    )
    return _out(conn, _row(conn, task_id))


def publish(conn: sqlite3.Connection, task_id: int) -> dict:
    row = _row(conn, task_id)
    if not row["confirmed"]:
        raise Conflict("сначала подтвердите карточку: публикуется только подтверждённая версия")
    if not json.loads(row["confirmed_card"] or "{}").get("title", "").strip():
        raise Conflict("у задачи нет названия — добавьте его и подтвердите карточку")
    conn.execute(
        "UPDATE task SET status = 'published', published_at = COALESCE(published_at, datetime('now')) WHERE id = ?",
        (task_id,),
    )
    return _out(conn, _row(conn, task_id))
