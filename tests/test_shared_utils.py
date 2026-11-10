"""Unit tests for the shared kernel."""

from dota_tracker.shared.utils import (
    chunk_list,
    clamp,
    format_duration,
    percentage,
    safe_div,
    to_datetime,
    utcnow,
)


def test_utcnow_returns_aware_datetime():
    result = utcnow()
    assert result.tzinfo is not None


def test_to_datetime_converts_epoch():
    assert to_datetime(0).year == 1970
    assert to_datetime(None) is None


def test_safe_div_zero_denominator():
    assert safe_div(10, 0) == 0.0
    assert safe_div(10, 2) == 5.0


def test_clamp():
    assert clamp(5, 0, 10) == 5
    assert clamp(-1, 0, 10) == 0
    assert clamp(15, 0, 10) == 10


def test_chunk_list():
    assert chunk_list([1, 2, 3, 4, 5], 2) == [[1, 2], [3, 4], [5]]
    assert chunk_list([], 3) == []


def test_format_duration():
    assert format_duration(0) == "0:00"
    assert format_duration(65) == "1:05"
    assert format_duration(3661) == "1:01:01"


def test_percentage():
    assert percentage(1, 2) == 50.0
    assert percentage(0, 0) == 0.0
