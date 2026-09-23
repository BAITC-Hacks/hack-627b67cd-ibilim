from app import ai, llm

DRAFT = "Хотим понимать, какие поля скоро потребуют полива. Пишите на agro@sever.kz"


def fake_llm(monkeypatch, response):
    monkeypatch.setattr(llm, "call_json", lambda *args, **kwargs: (response, 1))


def test_value_without_quote_is_dropped():
    card, sources, warnings = ai._verify(
        [{"field": "need", "value": "Сократить расход воды", "quote": "экономить воду на 30%"}], DRAFT
    )
    assert card == {} and sources == {}
    assert "цитата не найдена" in warnings[0]


def test_invented_number_is_dropped():
    card, _, warnings = ai._verify(
        [{"field": "context", "value": "Полив 120 полей", "quote": "какие поля скоро потребуют полива"}], DRAFT
    )
    assert card == {}
    assert "120" in warnings[0]


def test_quoted_value_is_kept_with_source():
    card, sources, warnings = ai._verify(
        [{"field": "contact", "value": "agro@sever.kz", "quote": "Пишите на agro@sever.kz"}], DRAFT
    )
    assert card == {"contact": "agro@sever.kz"}
    assert sources["contact"] == "Пишите на agro@sever.kz"
    assert warnings == []


def test_stub_asks_at_least_three_questions_without_inventing():
    result = ai.analyze_draft(DRAFT, "Агро")
    assert result["ai"]["mode"] == "stub"
    assert len(result["questions"]) >= ai.MIN_QUESTIONS
    assert result["card"]["context"] == DRAFT
    assert result["card"]["contact"] == "agro@sever.kz"
    assert {q["field"] for q in result["questions"]}.isdisjoint(result["card"])


def test_too_few_model_questions_are_topped_up(monkeypatch):
    fake_llm(monkeypatch, {"fields": [], "questions": [{"field": "data", "question": "Какие есть данные?"}]})
    result = ai.analyze_draft(DRAFT, "Агро")
    assert result["ai"]["mode"] == "llm"
    assert len(result["questions"]) == ai.MIN_QUESTIONS
    assert result["questions"][0]["text"] == "Какие есть данные?"
    assert any("добрали" in w for w in result["ai"]["warnings"])


def test_build_card_keeps_manual_fields_and_unplaced_answers(monkeypatch):
    fake_llm(monkeypatch, {"fields": [{"field": "title", "value": "Новый заголовок", "quote": "потребуют полива"}]})
    qa = [{"field": "data", "text": "Какие данные?", "answer": "CSV с датчиков за 2 года"}]
    result = ai.build_card(DRAFT, qa, {"title": "Заголовок бизнеса"}, {"title": "manual"})
    assert result["card"]["title"] == "Заголовок бизнеса"
    assert result["card"]["data"] == "CSV с датчиков за 2 года"
    assert result["sources"]["data"] == "CSV с датчиков за 2 года"


def test_spec_shows_prompts_and_schemas():
    spec = ai.spec()
    assert [c["name"] for c in spec["calls"]] == ["analyze_draft", "build_card"]
    assert all(c["system"] and c["output_schema"] for c in spec["calls"])
    assert spec["invalid_response"]
