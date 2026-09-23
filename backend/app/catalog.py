"""Общий каталог и рекомендации командам (ТЗ §3–4).

Владелец — Codex. Форматы — docs/02-api.md. Функции не делают commit: транзакцию закрывает роут.
"""

import json
import re
import sqlite3

from . import errors, rating


def _stem(word: str) -> str:
    return word[:5] if len(word) >= 5 else word


def _words(value: str) -> set[str]:
    return {_stem(word) for word in re.findall(r"\w+", value.lower(), re.UNICODE)}


def _summary(card: dict) -> str:
    value = (card.get("need") or card.get("context") or "").strip()
    return value if len(value) <= 160 else value[:159].rstrip() + "…"


def place(conn: sqlite3.Connection, score: int, task_id: int | None = None) -> dict:
    """Место задачи или прогноз для черновика среди опубликованных задач.

    Исключаем task_id из сравнения, чтобы опубликованная задача не считала себя дважды.
    Равный балл не увеличивает место; сортировка каталога разрешает ничью по времени.
    """
    row = conn.execute(
        "SELECT COUNT(*) AS others, COUNT(CASE WHEN score > ? THEN 1 END) AS ahead "
        "FROM task WHERE status = 'published' AND (? IS NULL OR id != ?)",
        (score, task_id, task_id),
    ).fetchone()
    return {"place": row["ahead"] + 1, "of": row["others"] + 1}


def listing(conn: sqlite3.Connection, industry: str | None = None, level: str | None = None) -> list[dict]:
    """GET /api/catalog. Все задачи со status = published — низкий рейтинг не скрывает задачу.

    Порядок: task.score по убыванию, при равенстве — published_at новее выше. Фильтры — точное
    совпадение industry и level. Заголовок и summary (~160 символов need или context) — из
    confirmed_card. needs_clarification = level draft, highlight = level priority,
    proposals — число откликов.
    """
    where = ["t.status = 'published'"]
    params = []
    if industry is not None:
        where.append("t.industry = ?")
        params.append(industry)
    if level is not None:
        where.append("t.level = ?")
        params.append(level)
    rows = conn.execute(
        "SELECT t.id, t.industry, t.confirmed_card, t.score, t.level, t.published_at, "
        "b.name AS business, (SELECT COUNT(*) FROM proposal AS p WHERE p.task_id = t.id) AS proposals "
        "FROM task AS t JOIN business AS b ON b.id = t.business_id "
        "WHERE " + " AND ".join(where) + " "
        "ORDER BY t.score DESC, t.published_at DESC, t.id DESC",
        params,
    )
    labels = {key: label for _, key, label in rating.LEVELS}
    result = []
    for row in rows:
        card = json.loads(row["confirmed_card"] or "{}")
        result.append({
            "id": row["id"], "title": card.get("title", ""), "industry": row["industry"],
            "business": row["business"], "summary": _summary(card), "score": row["score"],
            "level": row["level"], "level_label": labels.get(row["level"], ""),
            "needs_clarification": row["level"] == "draft",
            "highlight": row["level"] == "priority", "proposals": row["proposals"],
            "published_at": row["published_at"].replace(" ", "T") + "Z" if row["published_at"] else None,
        })
    return result


def recommend(conn: sqlite3.Connection, team_id: int, limit: int = 5) -> list[dict]:
    """GET /api/teams/{id}/recommendations. Опубликованные задачи уровня working и выше.

    match — слова команды (interests + skills + technologies), чьи основы есть в задаче
    (industry + текст confirmed_card). Основа слова длиной от 5 символов — первые 5 символов,
    короткие слова сравниваются целиком. Только задачи с непустым match; сортировка —
    длина match, затем score. Нет команды → errors.NotFound. Объяснимо, без LLM.
    """
    team = conn.execute(
        "SELECT interests, skills, technologies FROM team WHERE id = ?", (team_id,)
    ).fetchone()
    if team is None:
        raise errors.NotFound("Команда не найдена")
    team_words = []
    for field in ("interests", "skills", "technologies"):
        for phrase in json.loads(team[field] or "[]"):
            team_words.extend(re.findall(r"\w+", phrase.lower(), re.UNICODE))
    # Keep the team's wording and order in the explanation; count each stem once.
    team_stems = {}
    for word in team_words:
        team_stems.setdefault(_stem(word), word)

    matches = []
    rows = conn.execute(
        "SELECT id, industry, confirmed_card, score, level, published_at "
        "FROM task WHERE status = 'published' AND level IN ('working', 'ready', 'priority') "
        "ORDER BY score DESC, published_at DESC, id DESC"
    )
    for row in rows:
        card = json.loads(row["confirmed_card"] or "{}")
        task_words = _words(" ".join([row["industry"] or "", *(str(value) for value in card.values())]))
        common = [word for stem, word in team_stems.items() if stem in task_words]
        if common:
            matches.append((
                len(common),
                {"task_id": row["id"], "title": card.get("title", ""), "score": row["score"],
                 "level": row["level"], "match": common},
            ))
    matches.sort(key=lambda item: -item[0])
    return [item[1] for item in matches[:max(0, limit)]]
