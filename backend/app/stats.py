"""Панель программы AI Sana: сколько задач, насколько они готовы, какие отрасли, как бизнес отвечает студентам.

Владелец — Claude. Только агрегаты по БД, без персональных данных. Формат — docs/02-api.md.
"""

import json
import sqlite3

from . import rating


def overview(conn: sqlite3.Connection) -> dict:
    labels = {key: label for _, key, label in rating.LEVELS}
    t = conn.execute(
        "SELECT COUNT(*) AS total, SUM(status = 'published') AS published, "
        "ROUND(AVG(CASE WHEN status = 'published' THEN score END), 1) AS avg_score FROM task"
    ).fetchone()
    by_level = {key: 0 for _, key, _ in reversed(rating.LEVELS)}
    for r in conn.execute("SELECT level, COUNT(*) AS n FROM task WHERE status = 'published' GROUP BY level"):
        if r["level"] in by_level:
            by_level[r["level"]] = r["n"]
    industries = [
        dict(r) for r in conn.execute(
            "SELECT t.industry, COUNT(DISTINCT t.id) AS tasks, ROUND(AVG(t.score), 1) AS avg_score, "
            "COUNT(p.id) AS proposals FROM task AS t LEFT JOIN proposal AS p ON p.task_id = t.id "
            "WHERE t.status = 'published' GROUP BY t.industry ORDER BY tasks DESC, t.industry"
        )
    ]
    p = conn.execute(
        "SELECT COUNT(*) AS total, SUM(status = 'accepted') AS accepted, SUM(status = 'rejected') AS rejected, "
        "SUM(status = 'submitted') AS pending, "
        "ROUND(AVG(CASE WHEN decided_at IS NOT NULL THEN (julianday(decided_at) - julianday(created_at)) * 24 END), 1) AS hours "
        "FROM proposal"
    ).fetchone()
    # рост рейтинга от первого черновика до последнего подтверждения — эффект геймификации
    growth = conn.execute(
        "SELECT ROUND(AVG(last.score - first.score), 1) AS avg FROM "
        "(SELECT task_id, MIN(id) AS a, MAX(id) AS b FROM rating_event GROUP BY task_id HAVING COUNT(*) > 1) AS e "
        "JOIN rating_event AS first ON first.id = e.a JOIN rating_event AS last ON last.id = e.b"
    ).fetchone()["avg"]
    teams = [
        {"id": r["id"], "name": r["name"], "points": r["points"], "proposals": r["proposals"],
         "accepted": r["accepted"], "skills": json.loads(r["skills"])}
        for r in conn.execute(
            "SELECT tm.*, COUNT(p.id) AS proposals, COALESCE(SUM(p.status = 'accepted'), 0) AS accepted "
            "FROM team AS tm LEFT JOIN proposal AS p ON p.team_id = tm.id GROUP BY tm.id "
            "ORDER BY tm.points DESC, accepted DESC, proposals DESC, tm.id"
        )
    ]
    return {
        "tasks": {"total": t["total"], "published": t["published"] or 0, "avg_score": t["avg_score"],
                  "by_level": [{"key": k, "label": labels[k], "count": n} for k, n in by_level.items()],
                  "avg_growth": growth},
        "industries": industries,
        "proposals": {"total": p["total"], "accepted": p["accepted"] or 0, "rejected": p["rejected"] or 0,
                      "pending": p["pending"] or 0, "avg_hours_to_decision": p["hours"]},
        "teams": teams,
    }
