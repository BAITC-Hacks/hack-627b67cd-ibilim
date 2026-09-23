"""Некорректные ответы транспорта: реальные call_json/ai, без обращения к OpenAI."""

import json
from types import SimpleNamespace

import pytest

from app import ai, llm


def model_responses(monkeypatch, *responses):
    calls = []

    def create(**kwargs):
        calls.append(kwargs)
        content = responses[min(len(calls) - 1, len(responses) - 1)]
        message = SimpleNamespace(content=content)
        return SimpleNamespace(choices=[SimpleNamespace(message=message)])

    client = SimpleNamespace(chat=SimpleNamespace(completions=SimpleNamespace(create=create)))
    monkeypatch.setattr(llm, "mode", lambda: "llm")
    monkeypatch.setattr(llm, "client", lambda: client)
    return calls


@pytest.mark.parametrize("bad", [
    "not json", "null", "[]", "{}", '{"fields":"wrong type"}',
    '{"fields":[{"field":"data","value":"CSV"}]}',
    '{"fields":[{"field":"unknown","value":"CSV","quote":"CSV"}]}',
    '{"fields":[{"field":"data","value":123,"quote":"CSV"}]}',
    '{"fields":[],"extra":true}',
])
def test_bad_json_or_schema_retries_then_accepts_valid_response(monkeypatch, bad):
    good = {"fields": [{"field": "data", "value": "CSV", "quote": "CSV"}]}
    calls = model_responses(monkeypatch, bad, json.dumps(good))
    result, attempts = llm.call_json("build_card", "system", "user", ai.CARD_SCHEMA)
    assert result == good and attempts == len(calls) == 2
    assert "Предыдущий ответ отклонён" in calls[1]["messages"][-1]["content"]


@pytest.mark.parametrize("name,bad", [
    ("analyze", {"questions": [{"field": "data", "question": "Какие данные?"}]}),
    ("build", {"fields": "unexpected string"}),
    ("student", {"can_start": "false", "first_week": [], "assumptions": []}),
    ("assist", {"fields": [None]}),
])
def test_all_ai_functions_fall_back_after_three_invalid_responses(monkeypatch, name, bad):
    calls = model_responses(monkeypatch, json.dumps(bad))
    draft = "Нужен прогноз полива"
    if name == "analyze":
        result = ai.analyze_draft(draft, "Агро")
        assert len(result["questions"]) >= 3 and result["card"]["context"] == draft
    elif name == "build":
        result = ai.build_card(draft, [{"field": "data", "text": "Данные?", "answer": "SQL-выгрузка"}], {}, {})
        assert result["card"]["data"] == "SQL-выгрузка"
    elif name == "student":
        result = ai.student_check({"need": draft})
        assert result["can_start"] is False
    else:
        result = ai.assist(draft, {}, [{"field": "data", "hint": "Данные?"}])
        assert result["items"] == []
    assert result["ai"]["mode"] == "stub" and result["ai"]["attempts"] == len(calls) == 3


def test_boolean_field_rejects_a_number(monkeypatch):
    bad = {"can_start": 1, "first_week": ["Проверить данные"], "assumptions": []}
    calls = model_responses(monkeypatch, json.dumps(bad))
    result = ai.student_check({"data": "CSV"})
    assert result["ai"]["mode"] == "stub" and len(calls) == 3
