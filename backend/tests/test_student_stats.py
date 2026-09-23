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
