import pytest

from app import rating, tasks
from app.errors import BadRequest, Conflict, NotFound


def fake_score(card: dict) -> dict:
    """Заменитель формулы: здесь проверяется жизненный цикл, а не веса рейтинга."""
    score = min(100, 10 * sum(1 for v in card.values() if v))
    level = next(key for low, key, _ in rating.LEVELS if score >= low)
    return {"score": score, "level": level, "level_label": level, "breakdown": [], "missing": [], "next_best": []}


@pytest.fixture
def db(conn, monkeypatch):
    monkeypatch.setattr(rating, "score", fake_score)
    conn.execute("INSERT INTO business (id, name, industry) VALUES (99, 'ТОО «Тест»', 'Агро')")
    return conn


def test_full_scenario_draft_to_publication(db):
    task = tasks.create(db, 99, "Хотим понимать, какие поля скоро потребуют полива", "")
    assert task["status"] == "new" and task["industry"] == "Агро"
    assert len(task["questions"]) >= 3
    first = task["rating"]["score"]

    answers = [{"question_id": q["id"], "answer": f"ответ про {q['field']}"} for q in task["questions"]]
    task = tasks.answer(db, task["id"], answers)
    assert task["status"] == "card" and not task["confirmed"]
    assert task["rating"]["score"] > first

    task = tasks.edit(db, task["id"], {"title": "Прогноз полива", "constraints": "срок 2 недели"})
    assert task["sources"]["title"] == "manual" and task["sources"]["constraints"] == "manual"

    task = tasks.confirm(db, task["id"])
    assert task["confirmed"] and task["official"]["score"] == task["rating"]["score"]

    task = tasks.publish(db, task["id"])
    assert task["status"] == "published" and task["published_at"].endswith("Z")
    assert [h["event"] for h in task["history"]] == ["draft", "answers", "edit", "confirm"]


def test_edit_after_confirm_keeps_official_until_reconfirm(db):
    task = tasks.create(db, 99, "Нужен бот для заявок", "")
    task = tasks.edit(db, task["id"], {"title": "Бот заявок"})
    task = tasks.confirm(db, task["id"])
    official = task["official"]["score"]
    task = tasks.edit(db, task["id"], {"users": "операторы"})
    assert not task["confirmed"]
    assert task["official"]["score"] == official
    assert task["rating"]["score"] > official


def test_publish_requires_confirmed_card_with_title(db):
    task = tasks.create(db, 99, "Нужен бот для заявок", "")
    with pytest.raises(Conflict):
        tasks.publish(db, task["id"])
    tasks.edit(db, task["id"], {"title": ""})
    tasks.confirm(db, task["id"])
    with pytest.raises(Conflict):
        tasks.publish(db, task["id"])


def test_validation_errors(db):
    with pytest.raises(BadRequest):
        tasks.create(db, 99, "   ", "")
    with pytest.raises(NotFound):
        tasks.create(db, 12345, "текст", "")
    task = tasks.create(db, 99, "Нужен бот для заявок", "")
    with pytest.raises(BadRequest):
        tasks.edit(db, task["id"], {"salary": "1000"})
    with pytest.raises(BadRequest):
        tasks.answer(db, task["id"], [{"question_id": 777777, "answer": "x"}])


def test_iin_never_reaches_storage_or_ai(db, monkeypatch):
    seen = {}
    real = tasks.ai.analyze_draft
    monkeypatch.setattr(tasks.ai, "analyze_draft", lambda text, industry: seen.setdefault("text", text) and real(text, industry))
    task = tasks.create(db, 99, "Дадим выгрузку клиентов с ФИО, ИИН 900101300017", "")
    assert "900101300017" not in task["draft_text"] and "900101300017" not in seen["text"]
    kinds = {p["kind"] for p in task["privacy"]}
    assert kinds == {"iin", "personal_data"}
    task = tasks.edit(db, task["id"], {"constraints": "Данные передадим обезличенными"})
    assert {p["kind"] for p in task["privacy"]} == {"iin"}  # предупреждение снято, факт маскирования остался


def test_meta_levels_cover_0_to_100():
    levels = tasks.meta()["levels"]
    assert levels[0]["min"] == 0 and levels[-1]["max"] == 100
    assert all(a["max"] + 1 == b["min"] for a, b in zip(levels, levels[1:]))
