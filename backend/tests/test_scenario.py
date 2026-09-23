"""Обязательное демо ТЗ §11 целиком через API, в режиме заглушки (без ключа OpenAI):
слабый черновик → уточнение → рост рейтинга → публикация → отклик команды → ручное решение бизнеса.
Те же тексты — в сценарии демо docs/04-demo.md.
"""

import pytest
from fastapi.testclient import TestClient

from app import db
from app.main import app

DRAFT = "Хотим понимать, какие поля скоро потребуют полива"
ANSWERS = {
    "need": "Сократить расход воды на 20% за сезон и не пересушивать поля",
    "data": "Выгрузка с датчиков влажности почвы за 2 года, CSV, и карта полей",
    "expected_result": "Прототип дашборда с прогнозом полива на 7 дней по каждому полю",
    "success_criteria": "Точность прогноза влажности не ниже 80% на исторических данных",
}
EDIT = {
    "title": "Прогноз полива по полям",
    "users": "Агрономы хозяйства, 5 человек, планируют полив каждое утро",
    "constraints": "Срок 3 недели, только открытые библиотеки, данные не выносить за пределы хозяйства",
    "contact": "agro@sever.kz",
    "interaction_format": "Созвон раз в неделю, вопросы в Telegram, ответ в течение дня",
}


@pytest.fixture
def client(tmp_path, monkeypatch):
    monkeypatch.setattr(db, "DB_PATH", tmp_path / "scenario.db")
    with TestClient(app) as c:
        yield c


def test_mandatory_demo_end_to_end(client):
    business = next(b for b in client.get("/api/businesses").json() if b["industry"] == "Агро")
    team = next(t for t in client.get("/api/teams").json() if "агро" in t["interests"])

    # 1. слабый черновик: низкий рейтинг и не меньше трёх вопросов
    r = client.post("/api/tasks", json={"business_id": business["id"], "draft_text": DRAFT, "industry": "Агро"})
    assert r.status_code == 201
    task = r.json()
    assert task["rating"]["level"] == "draft" and len(task["questions"]) >= 3
    assert task["ai"]["mode"] == "stub"
    # черновик не рекомендуем, но видно, кому он подходит и что даст улучшение
    assert not task["audience"]["recommended"]
    assert team["name"] in [t["name"] for t in task["audience"]["teams"]]
    then = task["rating"]["next_best"][0]["then"]
    assert then["score"] > task["rating"]["score"] and then["place"] <= task["position"]["place"]

    # 2. ответы → карточка, рейтинг вырос
    answers = [{"question_id": q["id"], "answer": ANSWERS.get(q["field"], "")} for q in task["questions"]]
    task = client.post(f"/api/tasks/{task['id']}/answers", json={"answers": answers}).json()
    assert task["status"] == "card"

    # 3. бизнес дописывает по подсказкам — рейтинг ещё выше
    assert task["rating"]["next_best"], "подсказки, что добавить, должны быть"
    task = client.put(f"/api/tasks/{task['id']}/card", json={"card": EDIT}).json()
    scores = [h["score"] for h in task["history"]]
    assert scores == sorted(scores) and scores[-1] > scores[0]
    assert task["rating"]["score"] >= 70
    assert task["position"] == {"place": 1, "of": 6, "projected": True}  # «опубликуйте — будете первой»

    # 4. без подтверждения не публикуется, после — публикуется
    assert client.post(f"/api/tasks/{task['id']}/publish").status_code == 409
    task = client.post(f"/api/tasks/{task['id']}/confirm").json()
    assert task["official"]["score"] == task["rating"]["score"]
    task = client.post(f"/api/tasks/{task['id']}/publish").json()
    assert task["status"] == "published"
    assert task["position"] == {"place": 1, "of": 6, "projected": False}

    # 5. в каталоге на своём месте по рейтингу, команде рекомендуется
    catalog = client.get("/api/catalog").json()
    assert [c["score"] for c in catalog] == sorted((c["score"] for c in catalog), reverse=True)
    assert task["id"] in [c["id"] for c in catalog]
    recommended = client.get(f"/api/teams/{team['id']}/recommendations").json()
    assert task["id"] in [r["task_id"] for r in recommended]

    # 6. команда сама откликается
    r = client.post(f"/api/tasks/{task['id']}/proposals", json={
        "team_id": team["id"], "idea": "Модель влажности по датчикам и погоде",
        "plan": "1) разбор данных 2) модель 3) дашборд", "timeline": "3 недели",
        "link": "https://github.com/datacats/irrigation",
    })
    assert r.status_code == 201
    proposal = r.json()
    assert proposal["status"] == "submitted"

    # 7. бизнес вручную принимает; автоматического назначения нет
    listed = client.get(f"/api/tasks/{task['id']}/proposals").json()
    assert [p["id"] for p in listed] == [proposal["id"]]
    decided = client.post(f"/api/proposals/{proposal['id']}/decision", json={"decision": "accept"}).json()
    assert decided["status"] == "accepted"


def test_proposal_to_unpublished_task_is_rejected(client):
    business = client.get("/api/businesses").json()[0]
    team = client.get("/api/teams").json()[0]
    task = client.post("/api/tasks", json={"business_id": business["id"], "draft_text": DRAFT}).json()
    r = client.post(f"/api/tasks/{task['id']}/proposals", json={
        "team_id": team["id"], "idea": "идея", "plan": "план", "timeline": "неделя", "link": "https://x.kz",
    })
    assert r.status_code == 409
    assert r.json()["error"]["code"] == "conflict"


def test_team_reads_confirmed_snapshot_until_business_confirms_again(client):
    before = client.get("/api/catalog/4").json()
    assert before["rating"]["score"] == before["official"]["score"] == 94
    changed = client.put("/api/tasks/4/card", json={"card": {
        "title": "НЕ ПОДТВЕРЖДЁННЫЙ ТЕКСТ", "success_criteria": "",
    }}).json()
    assert changed["confirmed"] is False
    assert changed["rating"]["score"] != before["rating"]["score"]
    # Бизнес продолжает видеть свой черновик, команда и каталог — предыдущий снимок.
    assert client.get("/api/tasks/4").json()["card"] == changed["card"]
    public = client.get("/api/catalog/4").json()
    assert public == before
    assert "НЕ ПОДТВЕРЖДЁННЫЙ" not in str(public)
    assert not {"draft_text", "questions", "sources", "history", "ai"} & public.keys()
    entry = next(t for t in client.get("/api/catalog").json() if t["id"] == 4)
    assert entry["score"] == public["rating"]["score"]
    assert entry["title"] == public["card"]["title"]

    confirmed = client.post("/api/tasks/4/confirm").json()
    public = client.get("/api/catalog/4").json()
    assert public["card"] == confirmed["card"]
    assert public["rating"]["score"] == confirmed["official"]["score"]
    assert public["position"] == confirmed["position"]


def test_public_detail_hides_unpublished_tasks_but_keeps_low_rating(client):
    task = client.post("/api/tasks", json={"business_id": 1, "draft_text": DRAFT}).json()
    assert client.get(f"/api/catalog/{task['id']}").status_code == 404
    client.post(f"/api/tasks/{task['id']}/confirm")
    assert client.get(f"/api/catalog/{task['id']}").status_code == 404
    assert client.get("/api/catalog/99999").status_code == 404
    low = client.get("/api/catalog/1")
    assert low.status_code == 200 and low.json()["rating"]["score"] == 32
