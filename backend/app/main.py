"""AI Sana Challenge Hub — API. Контракт заморожен в docs/02-api.md, правки только через него."""

import json
from contextlib import asynccontextmanager, contextmanager
from http import HTTPStatus
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from starlette.exceptions import HTTPException as StarletteHTTPException

from . import ai, catalog, db, llm, proposals, rating, stats, tasks
from .errors import BadRequest, Conflict, NotFound

ROOT = Path(__file__).resolve().parents[2]
WEB_DIST = ROOT / "web" / "dist"

@asynccontextmanager
async def lifespan(app: FastAPI):
    db.init()
    yield


app = FastAPI(title="AI Sana Challenge Hub", version="0.2.0", lifespan=lifespan)


# --- ошибки в формате контракта: {"error": {"code": "...", "message": "..."}} -------------

def _error(status: int, code: str, message: str) -> JSONResponse:
    return JSONResponse({"error": {"code": code, "message": message}}, status_code=status)


@app.exception_handler(StarletteHTTPException)
async def http_error(request: Request, exc: StarletteHTTPException) -> JSONResponse:
    code = HTTPStatus(exc.status_code).phrase.lower().replace(" ", "_")  # 404 → not_found
    return _error(exc.status_code, code, str(exc.detail))


@app.exception_handler(RequestValidationError)
async def validation_error(request: Request, exc: RequestValidationError) -> JSONResponse:
    message = "; ".join(f"{'.'.join(map(str, e['loc']))}: {e['msg']}" for e in exc.errors())
    return _error(422, "validation_error", message)


@app.exception_handler(Exception)
async def internal_error(request: Request, exc: Exception) -> JSONResponse:
    return _error(500, "internal_error", str(exc))


def _domain_handler(status: int, code: str):
    async def handler(request: Request, exc: Exception) -> JSONResponse:
        return _error(status, code, str(exc) or code)
    return handler


# модули бросают доменные ошибки и ничего не знают про HTTP
for _exc, _status, _code in (
    (NotFound, 404, "not_found"),
    (Conflict, 409, "conflict"),
    (BadRequest, 400, "bad_request"),
    (NotImplementedError, 501, "not_implemented"),
):
    app.add_exception_handler(_exc, _domain_handler(_status, _code))


@contextmanager
def _tx():
    """Соединение на запрос: commit при успехе, rollback при ошибке. Модули сами не коммитят."""
    conn = db.connect()
    try:
        with conn:
            yield conn
    finally:
        conn.close()


# --- справочники -----------------------------------------------------------------------

@app.get("/api/health")
def health() -> dict:
    with _tx() as conn:
        n = conn.execute("SELECT COUNT(*) AS n FROM task").fetchone()["n"]
    return {"ok": True, "db": "ok" if n else "empty", "llm": llm.mode(), "version": app.version}


@app.get("/api/meta")
def meta() -> dict:
    return tasks.meta()


@app.get("/api/businesses")
def businesses() -> list[dict]:
    with _tx() as conn:
        return [dict(r) for r in conn.execute("SELECT id, name, industry FROM business ORDER BY id")]


@app.get("/api/teams")
def teams() -> list[dict]:
    with _tx() as conn:
        rows = conn.execute("SELECT * FROM team ORDER BY id").fetchall()
    return [
        {"id": r["id"], "name": r["name"], "interests": json.loads(r["interests"]),
         "skills": json.loads(r["skills"]), "technologies": json.loads(r["technologies"]),
         "points": r["points"]}
        for r in rows
    ]


# --- задача: черновик → вопросы → карточка → рейтинг → публикация -------------------------

class TaskIn(BaseModel):
    business_id: int
    draft_text: str
    industry: str = ""


class AnswerIn(BaseModel):
    question_id: int
    answer: str = ""


class AnswersIn(BaseModel):
    answers: list[AnswerIn]


class CardIn(BaseModel):
    card: dict[str, str]


@app.post("/api/tasks", status_code=201)
def create_task(payload: TaskIn) -> dict:
    with _tx() as conn:
        return tasks.create(conn, payload.business_id, payload.draft_text, payload.industry)


@app.get("/api/tasks")
def list_tasks(business_id: int) -> list[dict]:
    with _tx() as conn:
        return tasks.for_business(conn, business_id)


@app.get("/api/tasks/{task_id}")
def get_task(task_id: int) -> dict:
    with _tx() as conn:
        return tasks.get(conn, task_id)


@app.post("/api/tasks/{task_id}/answers")
def answer_questions(task_id: int, payload: AnswersIn) -> dict:
    with _tx() as conn:
        return tasks.answer(conn, task_id, [a.model_dump() for a in payload.answers])


@app.put("/api/tasks/{task_id}/card")
def edit_card(task_id: int, payload: CardIn) -> dict:
    with _tx() as conn:
        return tasks.edit(conn, task_id, payload.card)


@app.post("/api/tasks/{task_id}/confirm")
def confirm_task(task_id: int) -> dict:
    with _tx() as conn:
        return tasks.confirm(conn, task_id)


@app.post("/api/tasks/{task_id}/publish")
def publish_task(task_id: int) -> dict:
    with _tx() as conn:
        return tasks.publish(conn, task_id)


@app.post("/api/tasks/{task_id}/student-check")
def student_check(task_id: int) -> dict:
    with _tx() as conn:
        card = tasks.get(conn, task_id)["card"]
    return ai.student_check(card)  # вызов модели — вне транзакции


@app.post("/api/tasks/{task_id}/assist")
def assist_card(task_id: int) -> dict:
    with _tx() as conn:
        texts, card, weak = tasks.assist_input(conn, task_id)
    return tasks.assist_result(card, ai.assist(texts, card, weak))  # модель — вне транзакции


@app.get("/api/stats")
def program_stats() -> dict:
    with _tx() as conn:
        return stats.overview(conn)


@app.post("/api/rating/preview")
def rating_preview(payload: CardIn) -> dict:
    return rating.score(payload.card)


# --- каталог, отклики, выбор бизнеса ----------------------------------------------------

@app.get("/api/catalog")
def catalog_listing(industry: str | None = None, level: str | None = None) -> list[dict]:
    with _tx() as conn:
        return catalog.listing(conn, industry, level)


@app.get("/api/catalog/{task_id}")
def catalog_detail(task_id: int) -> dict:
    with _tx() as conn:
        return catalog.detail(conn, task_id)


@app.get("/api/teams/{team_id}/recommendations")
def recommendations(team_id: int) -> list[dict]:
    with _tx() as conn:
        return catalog.recommend(conn, team_id)


class ProposalIn(BaseModel):
    team_id: int
    idea: str
    plan: str
    timeline: str
    link: str


class DecisionIn(BaseModel):
    decision: str
    comment: str = ""


class MilestoneIn(BaseModel):
    title: str


@app.post("/api/tasks/{task_id}/proposals", status_code=201)
def create_proposal(task_id: int, payload: ProposalIn) -> dict:
    with _tx() as conn:
        return proposals.create(conn, task_id, payload.team_id, payload.idea, payload.plan,
                                payload.timeline, payload.link)


@app.get("/api/tasks/{task_id}/proposals")
def task_proposals(task_id: int) -> list[dict]:
    with _tx() as conn:
        return proposals.for_task(conn, task_id)


@app.get("/api/teams/{team_id}/proposals")
def team_proposals(team_id: int) -> list[dict]:
    with _tx() as conn:
        return proposals.for_team(conn, team_id)


@app.post("/api/proposals/{proposal_id}/decision")
def decide_proposal(proposal_id: int, payload: DecisionIn) -> dict:
    with _tx() as conn:
        return proposals.decide(conn, proposal_id, payload.decision, payload.comment)


@app.post("/api/proposals/{proposal_id}/milestones")
def add_milestone(proposal_id: int, payload: MilestoneIn) -> dict:
    with _tx() as conn:
        return proposals.add_milestone(conn, proposal_id, payload.title)


# --- ИИ: промпты, формат входа и выхода, обработка некорректного ответа (ТЗ §5) ------------

@app.get("/api/ai/spec")
def ai_spec() -> dict:
    return ai.spec()


# --- статика фронта (один сервис = одна ссылка) -----------------------------------------

if (WEB_DIST / "index.html").exists():
    if (WEB_DIST / "assets").is_dir():
        app.mount("/assets", StaticFiles(directory=WEB_DIST / "assets"), name="assets")

    @app.get("/{full_path:path}")
    def spa(full_path: str) -> FileResponse:
        if full_path.startswith("api/"):
            raise StarletteHTTPException(404, "Not Found")
        file = WEB_DIST / full_path
        return FileResponse(file if full_path and file.is_file() else WEB_DIST / "index.html")
