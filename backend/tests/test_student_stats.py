from fastapi.testclient import TestClient
import pytest

from app import ai, db, llm
from app.main import app


@pytest.fixture
def client(tmp_path, monkeypatch):
    monkeypatch.setattr(db, "DB_PATH", tmp_path / "s.db")
    with TestClient(app) as c:
        yield c


def test_student_check_stub_flags_empty_fields(client):
    r = client.post("/api/tasks", json={"business_id": 1, "draft_text": "Нужен бот для заявок"}).json()
    check = client.post(f"/api/tasks/{r['id']}/student-check").json()
    assert check["ai"]["mode"] == "stub" and not check["can_start"]
    assert {a["field"] for a in check["assumptions"]} >= {"data", "success_criteria"}


def test_student_check_llm_filters_unknown_fields(monkeypatch):
    monkeypatch.setattr(llm, "call_json", lambda *a, **k: ({"can_start": True, "first_week": ["разбор данных", " "],
        "assumptions": [{"field": "data", "assumption": "CSV", "question": "Какой формат?"},
                        {"field": "salary", "assumption": "x", "question": "y"}]}, 1))
    check = ai.student_check({"need": "бот"})
    assert [a["field"] for a in check["assumptions"]] == ["data"]
    assert check["can_start"] is False and check["first_week"] == ["разбор данных"]


def test_stats_overview(client):
    s = client.get("/api/stats").json()
    assert s["tasks"]["published"] == 5 and sum(l["count"] for l in s["tasks"]["by_level"]) == 5
    assert s["proposals"]["total"] >= 5 and len(s["teams"]) == 5 and s["industries"]


def test_assist_keeps_only_quoted_suggestions_that_raise_score(client, monkeypatch):
    t = client.post("/api/tasks", json={"business_id": 1, "draft_text": "Нужен бот для заявок, 300 заявок в день"}).json()
    monkeypatch.setattr(llm, "mode", lambda: "llm")
    monkeypatch.setattr(llm, "call_json", lambda *a, **k: ({"fields": [
        {"field": "need", "value": "Бот для заявок: 300 заявок в день", "quote": "Нужен бот для заявок, 300 заявок в день"},
        {"field": "data", "value": "Журнал 900 заявок в CSV", "quote": "300 заявок в день"},  # выдуманное число
    ]}, 1))
    r = client.post(f"/api/tasks/{t['id']}/assist").json()
    fields = [s["field"] for s in r["suggestions"]]
    assert "data" not in fields and all(s["gain"] > 0 for s in r["suggestions"])
    assert any("900" in w for w in r["ai"]["warnings"])


def test_assist_without_key_is_honest(client):
    t = client.post("/api/tasks", json={"business_id": 1, "draft_text": "Нужен бот для заявок"}).json()
    r = client.post(f"/api/tasks/{t['id']}/assist").json()
    assert r["suggestions"] == [] and r["ai"]["mode"] == "stub"
