import pytest

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
    assert [c["name"] for c in spec["calls"]] == ["analyze_draft", "build_card", "student_check", "assist_card"]
    assert all(c["system"] and c["output_schema"] for c in spec["calls"])
    assert spec["invalid_response"]


@pytest.mark.parametrize("source,value", [
    ("Хотим прогноз полива по данным датчиков влажности", "Данные хранятся в PostgreSQL и обновляются ежедневно"),
    ("Данных датчиков влажности нет", "Данные датчиков влажности есть"),
    ("Если получим согласие, предоставим выгрузку", "Предоставим выгрузку"),
    ("Нельзя выносить данные за пределы хозяйства", "Выносить данные за пределы хозяйства"),
    ("Операторы проверяют заявки клиентов", "Клиенты проверяют заявки операторов"),
    ("Есть выгрузка CSV?", "Есть выгрузка CSV"),
])
def test_value_must_be_supported_even_with_a_real_quote(source, value):
    card, sources, warnings = ai._verify([{"field": "data", "value": value, "quote": source}], source)
    assert card == sources == {}
    assert any("формулировка не подтверждена" in warning for warning in warnings)


def test_word_overlap_does_not_make_a_quote_real():
    source = "Мы пока не можем предоставить выгрузку данных клиентов"
    quote = "Мы можем предоставить выгрузку данных клиентов"
    card, _, warnings = ai._verify([{"field": "data", "value": quote, "quote": quote}], source)
    assert card == {} and "цитата не найдена" in warnings[0]


def test_number_must_match_whole_fact_not_substring():
    source = "Выгрузка содержит 180 строк"
    card, _, warnings = ai._verify(
        [{"field": "data", "value": "Выгрузка содержит 80 строк", "quote": source}], source)
    assert card == {} and "80" in warnings[0]


@pytest.mark.parametrize("field,text", [
    ("success_criteria", "Точность прогноза не ниже 80%"),
    ("data", "SQL-выгрузка"),
    ("data", "CSV, API"),
    ("constraints", "Нельзя выносить данные за пределы хозяйства"),
    ("data", "Если получим согласие, предоставим выгрузку"),
])
def test_honest_short_statements_and_conditions_are_kept(field, text):
    card, sources, warnings = ai._verify([{"field": field, "value": text, "quote": text}], text)
    assert card == sources == {field: text}
    assert warnings == []


def test_complete_sentences_can_be_selected_from_a_longer_source():
    source = "Работаем вручную. Датчики дают CSV за 2 года. Нужен прогноз полива."
    text = "Датчики дают CSV за 2 года."
    card, _, warnings = ai._verify([{"field": "data", "value": text, "quote": text}], source)
    assert card == {"data": text} and not warnings


def test_assistant_can_move_a_supported_criterion_into_an_empty_field(monkeypatch):
    from app import tasks

    criterion = "Точность прогноза не ниже 80%."
    source = f"Нужен прогноз полива. {criterion}"
    card = {"context": source, "success_criteria": ""}
    fake_llm(monkeypatch, {"fields": [
        {"field": "success_criteria", "value": criterion, "quote": criterion},
    ]})
    result = ai.assist(source, card, [{"field": "success_criteria", "hint": "Назовите метрику"}])
    suggestions = tasks.assist_result(card, result)["suggestions"]
    assert len(suggestions) == 1
    assert suggestions[0]["value"] == suggestions[0]["quote"] == criterion
    assert suggestions[0]["gain"] == 15
