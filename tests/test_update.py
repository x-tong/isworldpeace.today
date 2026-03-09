import json
from pathlib import Path

from update import parse_conflicts, build_status

FIXTURE = Path(__file__).parent / "fixtures" / "conflicts.html"


def test_parse_conflicts_returns_dict_with_categories():
    html = FIXTURE.read_text()
    result = parse_conflicts(html)
    assert isinstance(result, dict)
    assert "total" in result
    assert result["total"] > 0
    assert "conflicts" in result
    assert isinstance(result["conflicts"], dict)


def test_parse_conflicts_counts_match_total():
    html = FIXTURE.read_text()
    result = parse_conflicts(html)
    category_sum = sum(result["conflicts"].values())
    assert category_sum == result["total"]


def test_build_status_structure():
    conflicts_data = {
        "total": 5,
        "conflicts": {"major_wars": 1, "wars": 2, "minor_conflicts": 2},
    }
    status = build_status(conflicts_data)
    assert status["peace"] is False
    assert status["total"] == 5
    assert "date" in status
    assert "day_counter" in status
    assert isinstance(status["day_counter"], int)
    assert status["day_counter"] > 0


def test_build_status_peace_when_zero():
    conflicts_data = {"total": 0, "conflicts": {}}
    status = build_status(conflicts_data)
    assert status["peace"] is True
