import pytest

from nettop.config import parse_duration


@pytest.mark.parametrize(
    "value,expected",
    [
        ("30s", 30),
        ("1m", 60),
        ("5m", 300),
        ("2h", 7200),
        ("1d", 86400),
        ("45", 45),
    ],
)
def test_parse_duration(value, expected):
    assert parse_duration(value) == expected


def test_parse_duration_invalid():
    with pytest.raises(ValueError):
        parse_duration("")
