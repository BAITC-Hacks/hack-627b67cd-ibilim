import json

import pytest

from app import catalog
from app.errors import NotFound


def test_listing_is_official_sorted_and_keeps_low_score(conn):
    items = catalog.listing(conn)
    assert [item["id"] for item in items] == [4, 5, 3, 2, 1]
    assert [item["score"] for item in items] == [94, 87, 80, 62, 32]
    assert items[-1]["needs_clarification"] is True
    assert items[0]["highlight"] is True
    assert items[-1]["proposals"] == 1
    assert all(len(item["summary"]) <= 160 for item in items)


def test_listing_filters_and_uses_confirmed_card(conn):
    conn.execute(
        "UPDATE task SET card = ? WHERE id = 3",
        (json.dumps({"title": "Неподтверждённая правка", "need": "Иной текст"}),),
    )
    item = catalog.listing(conn, industry="Логистика", level="ready")[0]
    assert item["title"] == "Планировщик маршрутов"
    assert "Неподтверждённая" not in item["summary"]
    assert catalog.listing(conn, industry="Логистика", level="draft") == []


def test_listing_tie_newer_first_and_unpublished_hidden(conn):
    conn.execute("UPDATE task SET score = 94, published_at = '2026-09-24 10:00:00' WHERE id = 2")
    assert [item["id"] for item in catalog.listing(conn)[:2]] == [2, 4]
    conn.execute("UPDATE task SET status = 'card' WHERE id = 2")
    assert 2 not in [item["id"] for item in catalog.listing(conn)]


def test_recommend_matches_words_and_excludes_draft(conn):
    # The only agricultural task is a published draft; it stays in the catalog.
    assert catalog.recommend(conn, 1) == []
    recommendations = catalog.recommend(conn, 3)
    assert recommendations[0]["task_id"] == 3
    assert "логистика" in recommendations[0]["match"]
    assert all(item["level"] != "draft" for item in recommendations)


def test_recommend_sorts_match_count_then_score_and_honors_limit(conn):
    conn.execute(
        "UPDATE team SET interests = ?, skills = '[]', technologies = '[]' WHERE id = 4",
        (json.dumps(["панель", "образование"], ensure_ascii=False),),
    )
    items = catalog.recommend(conn, 4)
    assert [item["task_id"] for item in items] == [4, 5, 3, 2]
    assert items[0]["match"] == ["панель", "образование"]
    assert len(catalog.recommend(conn, 4, limit=2)) == 2


def test_recommend_missing_team(conn):
    with pytest.raises(NotFound):
        catalog.recommend(conn, -1)
