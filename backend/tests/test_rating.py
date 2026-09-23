import pytest

from app import rating


FULL = {
    "title": "Прогноз полива по полям",
    "context": "Полив 120 полей сейчас планируют вручную",
    "need": "Нужен прогноз для 120 полей на 7 дней",
    "data": "Выгрузка датчиков влажности за 2 года, 25000 строк CSV",
    "expected_result": "Панель прогноза полива для 120 полей на неделю",
    "success_criteria": "Точность прогноза не ниже 85%",
    "constraints": "Бюджет до 500000 тенге, срок 2 месяца",
    "users": "Агрономы хозяйства планируют полив каждого поля",
    "contact": "project@example.kz",
    "interaction_format": "Еженедельные встречи с руководителем проекта",
}


def test_empty_card_is_zero_with_all_indicators_missing():
    result = rating.score({})
    assert result["score"] == 0
    assert result["level"] == "draft"
    assert len(result["breakdown"]) == len(result["missing"]) == 7
    assert result["next_best"][0]["gain"] == 20


def test_full_card_is_100_and_has_no_hints():
    result = rating.score(FULL)
    assert result["score"] == 100
    assert result["level"] == "priority"
    assert result["missing"] == result["next_best"] == []
    assert result["next_level"] is None
    assert result["penalties"] == []
    assert all(row["points"] == row["max"] and not row["hint"] for row in result["breakdown"])


@pytest.mark.parametrize(
    ("fields", "expected"),
    [
        ((), {"key": "working", "label": "рабочая", "points_needed": 40}),
        (("context", "need", "data"), {"key": "ready", "label": "готовая", "points_needed": 30}),
        (("context", "need", "data", "expected_result", "success_criteria"),
         {"key": "priority", "label": "приоритетная", "points_needed": 20}),
    ],
)
def test_next_level_uses_next_threshold(fields, expected):
    result = rating.score({field: FULL[field] for field in fields})
    assert result["next_level"] == expected


def test_partial_points_and_gain_order():
    result = rating.score({"context": "Полив планируют вручную", "data": "Датчики влажности"})
    by_key = {row["key"]: row for row in result["breakdown"]}
    assert by_key["context_need"]["points"] == 6
    assert by_key["data"]["points"] == 14
    assert result["score"] == 20
    assert "+6" in by_key["context_need"]["explain"]
    assert by_key["context_need"]["hint"]
    assert [row["gain"] for row in result["next_best"]] == sorted(
        [row["gain"] for row in result["next_best"]], reverse=True
    )


@pytest.mark.parametrize(
    ("first", "second"),
    [
        ("Полив 120 полей сейчас планируют вручную каждое утро по графику",
         "Полив 120 полей сейчас планируют вручную каждое утро по графику"),
        ("Полив 120 полей сейчас планируют вручную каждое утро по графику",
         "Полив 120 полей сейчас планируют вручную каждое утро по графику регулярно"),
        ("Полив 120 полей планируют вручную", "Полив 120 полей планируют ежедневно"),
    ],
)
def test_duplicate_text_is_counted_once(first, second):
    result = rating.score({"context": first, "need": second})
    assert result["score"] == 10
    assert result["penalties"] == [{
        "key": "duplicate", "label": "Повтор текста", "points": 10,
        "explain": "Поля «Контекст» и «Потребность» почти совпадают — текст засчитан один раз",
    }]
    assert result["score"] == sum(item["points"] for item in result["breakdown"]) - sum(
        item["points"] for item in result["penalties"]
    )


@pytest.mark.parametrize(
    ("field", "value", "points"),
    [("data", "csv api excel json", 9), ("success_criteria", "точность скорость", 3)],
)
def test_keyword_soup_loses_only_source_format_or_metric_bonus(field, value, points):
    result = rating.score({field: value})
    assert [(item["key"], item["points"]) for item in result["penalties"]] == [
        ("keyword_soup", points)
    ]
    assert result["score"] == sum(item["points"] for item in result["breakdown"]) - points


@pytest.mark.parametrize(
    ("field", "value"),
    [("context", "см. выше"), ("need", "уточним позже"),
     ("expected_result", "аналогично"), ("data", "tbd"), ("constraints", "todo")],
)
def test_filler_field_earns_no_points(field, value):
    result = rating.score({field: value})
    assert result["score"] == 0
    assert result["penalties"][0]["key"] == "filler"
    assert result["penalties"][0]["points"] == sum(item["points"] for item in result["breakdown"])


@pytest.mark.parametrize("value", ["кртмпл", "аааааа"])
def test_gibberish_field_earns_no_points(value):
    result = rating.score({"users": value})
    assert result["score"] == 0
    assert result["penalties"][0]["key"] == "gibberish"
    assert result["penalties"][0]["points"] == 6


def test_short_honest_success_criterion_is_not_penalized():
    result = rating.score({"success_criteria": "точность прогноза не ниже 80%"})
    assert result["score"] == 15
    assert result["penalties"] == []


def test_combined_penalties_reconcile_with_breakdown_and_next_level():
    result = rating.score({
        "context": "см. выше", "need": "см. выше",
        "data": "csv api excel json", "users": "кртмпл",
    })
    assert {item["key"] for item in result["penalties"]} == {
        "filler", "gibberish", "keyword_soup",
    }
    assert result["score"] == max(
        0, sum(item["points"] for item in result["breakdown"])
        - sum(item["points"] for item in result["penalties"]),
    ) == 8
    assert result["next_level"]["points_needed"] == 32


@pytest.mark.parametrize("placeholder", ["-", "—", "нет", "не знаю", "?", " нет. "])
def test_placeholders_do_not_earn_points(placeholder):
    result = rating.score({key: placeholder for key in rating.FIELDS})
    assert result["score"] == 0


@pytest.mark.parametrize(
    ("value", "expected"),
    [(0, "draft"), (39, "draft"), (40, "working"), (69, "working"),
     (70, "ready"), (89, "ready"), (90, "priority"), (100, "priority")],
)
def test_level_thresholds(value, expected):
    assert rating.level(value)[0] == expected
