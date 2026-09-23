import pytest

from app import proposals
from app.errors import BadRequest, Conflict, NotFound


def test_create_on_low_rated_published_task_and_no_commit(conn):
    result = proposals.create(
        conn, 1, 2, "Пилот прогноза", "1) данные 2) модель", "2 недели",
        "https://example.com/pilot",
    )
    assert result["task_id"] == 1
    assert result["team"] == {
        "id": 2, "name": "Retail Pulse",
        "skills": ["аналитика", "дизайн"], "technologies": ["React", "SQL"],
    }
    assert result["status"] == "submitted"
    assert result["comment"] == ""
    assert result["decided_at"] is None
    created_at = conn.execute("SELECT created_at FROM proposal WHERE id = ?", (result["id"],)).fetchone()[0]
    assert result["created_at"] == created_at.replace(" ", "T") + "Z"
    assert conn.in_transaction
    assert len(proposals.for_task(conn, 1)) == 2


@pytest.mark.parametrize("field", ["idea", "plan", "timeline"])
def test_create_requires_nonempty_content(conn, field):
    values = {"idea": "идея", "plan": "план", "timeline": "2 недели", "link": "https://example.com"}
    values[field] = "  "
    with pytest.raises(BadRequest):
        proposals.create(conn, 1, 2, **values)


@pytest.mark.parametrize("link", ["example.com", "ftp://example.com", "http://", "https://bad host"])
def test_create_validates_link(conn, link):
    with pytest.raises(BadRequest):
        proposals.create(conn, 1, 2, "идея", "план", "2 недели", link)


def test_create_missing_references_and_unpublished_task(conn):
    with pytest.raises(NotFound):
        proposals.create(conn, -1, 1, "идея", "план", "2 недели", "https://example.com")
    with pytest.raises(NotFound):
        proposals.create(conn, 1, -1, "идея", "план", "2 недели", "https://example.com")
    conn.execute("UPDATE task SET status = 'card' WHERE id = 1")
    with pytest.raises(Conflict):
        proposals.create(conn, 1, 1, "идея", "план", "2 недели", "https://example.com")


def test_views_order_and_not_found(conn):
    first = proposals.create(conn, 1, 2, "первая", "план", "2 недели", "https://example.com/1")
    second = proposals.create(conn, 1, 2, "вторая", "план", "2 недели", "https://example.com/2")
    task_rows = proposals.for_task(conn, 1)
    team_rows = proposals.for_team(conn, 2)
    assert [row["id"] for row in task_rows][-2:] == [first["id"], second["id"]]
    assert [row["id"] for row in team_rows][:2] == [second["id"], first["id"]]
    assert task_rows[-1]["team"] == team_rows[0]["team"] == first["team"]
    with pytest.raises(NotFound):
        proposals.for_task(conn, -1)
    with pytest.raises(NotFound):
        proposals.for_team(conn, -1)


def test_business_can_accept_multiple_proposals_manually(conn):
    another = proposals.create(conn, 1, 2, "другой план", "пилот", "3 недели", "https://example.com")
    accepted_seed = proposals.decide(conn, 1, "accept", "Подходит")
    accepted_new = proposals.decide(conn, another["id"], "accept", "Тоже подходит")
    assert accepted_seed["status"] == accepted_new["status"] == "accepted"
    assert accepted_new["team"] == another["team"]
    assert accepted_seed["comment"] == "Подходит"
    assert accepted_seed["decided_at"] is not None
    decided_at = conn.execute("SELECT decided_at FROM proposal WHERE id = 1").fetchone()[0]
    assert accepted_seed["decided_at"] == decided_at.replace(" ", "T") + "Z"
    assert conn.execute("SELECT COUNT(*) FROM proposal WHERE task_id = 1 AND status = 'accepted'").fetchone()[0] == 2


def test_decide_rejects_invalid_value_and_missing_proposal(conn):
    with pytest.raises(BadRequest):
        proposals.decide(conn, 1, "maybe")
    with pytest.raises(NotFound):
        proposals.decide(conn, -1, "accept")
    rejected = proposals.decide(conn, 1, "reject", "Нужен другой срок")
    assert rejected["status"] == "rejected"


def test_milestone_only_after_acceptance_and_awards_team(conn):
    with pytest.raises(Conflict):
        proposals.add_milestone(conn, 1, "Пилот")
    proposals.decide(conn, 1, "accept")
    assert proposals.add_milestone(conn, 1, "Пилот") == {"proposal_id": 1, "team_points": 10}
    assert proposals.add_milestone(conn, 1, "Проверка", points=5) == {"proposal_id": 1, "team_points": 15}
    assert conn.execute("SELECT COUNT(*) FROM milestone WHERE proposal_id = 1").fetchone()[0] == 2
    with pytest.raises(BadRequest):
        proposals.add_milestone(conn, 1, " ")
