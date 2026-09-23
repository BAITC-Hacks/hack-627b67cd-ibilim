"""iBilim API. Контракт заморожен в docs/04-api.md — правки только через него.

Роуты ниже реализованы по минимуму (health, классы, план); остальные — заглушки с
правильными сигнатурами, чтобы фронт мог подключаться сразу, а логика доезжала следом.
"""

import json
import os
from pathlib import Path

from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.responses import FileResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from . import db

ROOT = Path(__file__).resolve().parents[2]
WEB_DIST = ROOT / "web" / "dist"

app = FastAPI(title="iBilim", version="0.1.0")


@app.on_event("startup")
def startup() -> None:
    db.init()


@app.get("/api/health")
def health() -> dict:
    conn = db.connect()
    objectives = conn.execute("SELECT COUNT(*) AS n FROM objective").fetchone()["n"]
    conn.close()
    return {
        "ok": True,
        "db": "ok" if objectives else "empty",
        "llm": "demo" if os.getenv("DEMO_MODE") == "1" else "live",
        "version": app.version,
    }


@app.get("/api/classes")
def classes() -> list[dict]:
    conn = db.connect()
    rows = conn.execute(
        """SELECT k.id, k.name, k.subject, k.grade, k.language,
                  (SELECT COUNT(*) FROM student s WHERE s.klass_id = k.id) AS students
           FROM klass k"""
    ).fetchall()
    conn.close()
    return [dict(row) for row in rows]


@app.get("/api/classes/{class_id}/plan")
def plan(class_id: int) -> dict:
    conn = db.connect()
    klass = conn.execute("SELECT * FROM klass WHERE id = ?", (class_id,)).fetchone()
    if klass is None:
        conn.close()
        raise HTTPException(404, "class not found")
    lessons = conn.execute(
        """SELECT l.id, l.date, l.topic, l.objective_codes, l.status,
                  (SELECT COUNT(*) FROM lesson_pack p WHERE p.lesson_id = l.id) AS packs
           FROM lesson l WHERE l.klass_id = ? ORDER BY l.date""",
        (class_id,),
    ).fetchall()
    conn.close()
    return {
        "class": {"id": klass["id"], "name": klass["name"], "subject": klass["subject"]},
        "quarter": 1,
        "lessons": [
            {
                "id": row["id"],
                "date": row["date"],
                "topic": row["topic"],
                "objectives": json.loads(row["objective_codes"]),
                "status": row["status"],
                "has_pack": bool(row["packs"]),
            }
            for row in lessons
        ],
    }


# --- ниже: заглушки под контракт, реализуются в ходе хакатона -------------------------

@app.post("/api/classes/{class_id}/plan/build")
def build_plan(class_id: int) -> dict:
    """planner.build(class_id) → создаёт lesson на четверть. См. docs/06-pipelines.md §2."""
    raise HTTPException(501, "planner not implemented yet")


@app.get("/api/lessons/{lesson_id}")
def lesson(lesson_id: int) -> dict:
    raise HTTPException(501, "not implemented yet")


@app.post("/api/lessons/{lesson_id}/pack")
def lesson_pack(lesson_id: int, force: bool = False) -> dict:
    """generate.lesson_pack(...) → КСП, объяснение, задания, шаблоны ДЗ. docs/05-llm.md §1."""
    raise HTTPException(501, "not implemented yet")


@app.post("/api/lessons/{lesson_id}/homework")
def build_homework(lesson_id: int) -> dict:
    """60% цели урока + 40% просевшие цели, seed на ученика. docs/06-pipelines.md §3."""
    raise HTTPException(501, "not implemented yet")


@app.get("/api/students/{student_id}/homework")
def student_homework(student_id: int, lesson_id: int) -> dict:
    raise HTTPException(501, "not implemented yet")


class AnswerIn(BaseModel):
    item_id: int
    answer: str
    telemetry: dict = {}


class SubmissionIn(BaseModel):
    student_id: int
    lesson_id: int
    channel: str = "web"
    answers: list[AnswerIn]


@app.post("/api/submissions")
def submit(payload: SubmissionIn) -> dict:
    """grade.check(...) → sympy, дескрипторы, mastery, детектор. docs/06-pipelines.md §4–5."""
    raise HTTPException(501, "not implemented yet")


@app.post("/api/submissions/photo")
async def submit_photo(
    file: UploadFile = File(...),
    student_id: int = Form(...),
    lesson_id: int = Form(...),
    channel: str = Form("phone"),
) -> dict:
    raise HTTPException(501, "not implemented yet")


@app.get("/api/students/{student_id}/mastery")
def student_mastery(student_id: int) -> dict:
    raise HTTPException(501, "not implemented yet")


@app.get("/api/classes/{class_id}/mastery")
def class_mastery(class_id: int) -> dict:
    raise HTTPException(501, "not implemented yet")


@app.get("/api/teacher/review-queue")
def review_queue(class_id: int) -> list[dict]:
    raise HTTPException(501, "not implemented yet")


@app.get("/api/print/homework/{lesson_id}", response_class=HTMLResponse)
def print_homework(lesson_id: int) -> str:
    """HTML для печати: лист на ученика, QR в углу, разрыв страницы. MVP-2."""
    raise HTTPException(501, "not implemented yet")


# --- статика фронта (один сервис = одна публичная ссылка) ------------------------------

if WEB_DIST.exists():
    app.mount("/assets", StaticFiles(directory=WEB_DIST / "assets"), name="assets")

    @app.get("/{full_path:path}")
    def spa(full_path: str) -> FileResponse:
        return FileResponse(WEB_DIST / "index.html")
