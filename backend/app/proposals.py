"""Отклики команд и ручной выбор бизнеса. Автоматического назначения нет (ТЗ §3, §5).

Владелец — Codex. Форматы — объект Proposal в docs/02-api.md.
Функции не делают commit: транзакцию закрывает роут в main.py.
"""

import sqlite3
from urllib.parse import urlsplit

from . import errors


def _proposal(row: sqlite3.Row) -> dict:
    return {
        "id": row["id"], "task_id": row["task_id"],
        "team": {"id": row["team_id"], "name": row["team_name"]},
        "idea": row["idea"], "plan": row["plan"], "timeline": row["timeline"],
        "link": row["link"], "status": row["status"], "comment": row["comment"],
        "created_at": row["created_at"].replace(" ", "T"),
        "decided_at": row["decided_at"].replace(" ", "T") if row["decided_at"] else None,
    }


def _get(conn: sqlite3.Connection, proposal_id: int) -> dict:
    row = conn.execute(
        "SELECT p.*, t.name AS team_name FROM proposal AS p "
        "JOIN team AS t ON t.id = p.team_id WHERE p.id = ?",
        (proposal_id,),
    ).fetchone()
    if row is None:
        raise errors.NotFound("Отклик не найден")
    return _proposal(row)


def create(conn: sqlite3.Connection, task_id: int, team_id: int, idea: str, plan: str, timeline: str, link: str) -> dict:
    """POST /api/tasks/{id}/proposals → Proposal. Число откликов не ограничено.

    Нет задачи или команды → errors.NotFound; задача не опубликована → errors.Conflict;
    пустые idea / plan / timeline или link не http(s):// → errors.BadRequest.
    """
    task = conn.execute("SELECT status FROM task WHERE id = ?", (task_id,)).fetchone()
    if task is None:
        raise errors.NotFound("Задача не найдена")
    if conn.execute("SELECT 1 FROM team WHERE id = ?", (team_id,)).fetchone() is None:
        raise errors.NotFound("Команда не найдена")
    if task["status"] != "published":
        raise errors.Conflict("Отклик возможен только на опубликованную задачу")
    idea, plan, timeline, link = (value.strip() for value in (idea, plan, timeline, link))
    if not idea or not plan or not timeline:
        raise errors.BadRequest("Идея, план и срок обязательны")
    parsed = urlsplit(link)
    if parsed.scheme not in ("http", "https") or not parsed.netloc or any(char.isspace() for char in link):
        raise errors.BadRequest("Ссылка должна начинаться с http(s):// и содержать адрес")
    cursor = conn.execute(
        "INSERT INTO proposal (task_id, team_id, idea, plan, timeline, link) "
        "VALUES (?, ?, ?, ?, ?, ?)",
        (task_id, team_id, idea, plan, timeline, link),
    )
    return _get(conn, cursor.lastrowid)


def for_task(conn: sqlite3.Connection, task_id: int) -> list[dict]:
    """GET /api/tasks/{id}/proposals — старые сверху. Нет задачи → errors.NotFound."""
    if conn.execute("SELECT 1 FROM task WHERE id = ?", (task_id,)).fetchone() is None:
        raise errors.NotFound("Задача не найдена")
    rows = conn.execute(
        "SELECT p.*, t.name AS team_name FROM proposal AS p "
        "JOIN team AS t ON t.id = p.team_id WHERE p.task_id = ? "
        "ORDER BY p.created_at, p.id",
        (task_id,),
    )
    return [_proposal(row) for row in rows]


def for_team(conn: sqlite3.Connection, team_id: int) -> list[dict]:
    """GET /api/teams/{id}/proposals — новые сверху. Нет команды → errors.NotFound."""
    if conn.execute("SELECT 1 FROM team WHERE id = ?", (team_id,)).fetchone() is None:
        raise errors.NotFound("Команда не найдена")
    rows = conn.execute(
        "SELECT p.*, t.name AS team_name FROM proposal AS p "
        "JOIN team AS t ON t.id = p.team_id WHERE p.team_id = ? "
        "ORDER BY p.created_at DESC, p.id DESC",
        (team_id,),
    )
    return [_proposal(row) for row in rows]


def decide(conn: sqlite3.Connection, proposal_id: int, decision: str, comment: str = "") -> dict:
    """POST /api/proposals/{id}/decision → Proposal. decision: accept | reject, иначе errors.BadRequest.

    status = accepted | rejected, comment, decided_at = now. Можно принять несколько откликов.
    """
    if decision not in ("accept", "reject"):
        raise errors.BadRequest("Решение должно быть accept или reject")
    _get(conn, proposal_id)
    conn.execute(
        "UPDATE proposal SET status = ?, comment = ?, decided_at = datetime('now') WHERE id = ?",
        ("accepted" if decision == "accept" else "rejected", comment, proposal_id),
    )
    return _get(conn, proposal_id)


def add_milestone(conn: sqlite3.Connection, proposal_id: int, title: str, points: int = 10) -> dict:
    """MVP-2. POST /api/proposals/{id}/milestones → {"proposal_id", "team_points"}.

    Только для accepted, иначе errors.Conflict. team.points += points.
    """
    proposal = _get(conn, proposal_id)
    if proposal["status"] != "accepted":
        raise errors.Conflict("Этап можно подтвердить только у принятого отклика")
    if not title.strip() or points <= 0:
        raise errors.BadRequest("Название этапа и положительное число баллов обязательны")
    conn.execute(
        "INSERT INTO milestone (proposal_id, title, points) VALUES (?, ?, ?)",
        (proposal_id, title.strip(), points),
    )
    conn.execute("UPDATE team SET points = points + ? WHERE id = ?", (points, proposal["team"]["id"]))
    total = conn.execute("SELECT points FROM team WHERE id = ?", (proposal["team"]["id"],)).fetchone()["points"]
    return {"proposal_id": proposal_id, "team_points": total}
