import pytest

from error_events import (
    MAX_EVENTS,
    MAX_MESSAGE_CHARS,
    detect_category,
    detect_severity,
    extract_error_events,
    normalize_message,
)


def test_empty_input_returns_empty_list():
    assert extract_error_events("") == []


def test_log_without_errors_returns_empty_list():
    assert extract_error_events("INFO started\nINFO listening on 8000") == []


def test_same_error_with_different_timestamps_is_grouped():
    log = (
        "2026-11-25 10:01:05 ERROR DB timeout after 30s\n"
        "2026-11-25 10:01:07 ERROR DB timeout after 30s\n"
        "2026-11-25 10:01:09 ERROR DB timeout after 30s\n"
    )
    events = extract_error_events(log)
    assert len(events) == 1
    assert events[0].repeat_count == 3
    assert events[0].category == "timeout"
    assert events[0].severity == "ERROR"


def test_numbers_do_not_split_groups():
    assert normalize_message("ERROR timeout after 30s") == normalize_message(
        "ERROR timeout after 60s"
    )


def test_events_sorted_by_repeat_count_then_first_seen():
    log = "ERROR a failed\nERROR b timeout\nERROR b timeout\nERROR c failed\n"
    counts = [(e.message, e.repeat_count) for e in extract_error_events(log)]
    assert counts[0] == ("ERROR b timeout", 2)
    assert [m for m, _ in counts[1:]] == ["ERROR a failed", "ERROR c failed"]


@pytest.mark.parametrize(
    "line,expected",
    [
        ("ERROR DB timeout after 30s", "timeout"),
        ("request timed out", "timeout"),
        ("ERROR connection refused by host", "connection"),
        ("FATAL could not connect to database", "connection"),  # beats crash
        ("ERROR deadlock detected", "database"),
        ("CRITICAL out of memory", "memory"),
        ("ERROR 401 unauthorized", "auth"),
        ("Traceback (most recent call last):", "crash"),
        ("Segmentation fault", "crash"),
        ("ERROR something odd happened", "other"),
    ],
)
def test_category_rules(line, expected):
    assert detect_category(line) == expected


@pytest.mark.parametrize(
    "line,expected",
    [
        ("ERROR something", "ERROR"),
        ("fatal: boom", "FATAL"),
        ("CRITICAL disk full", "CRITICAL"),
        ("ERROR then FATAL on one line", "FATAL"),   # most severe wins
        ("request failed with status 500", None),    # no level token
    ],
)
def test_severity(line, expected):
    assert detect_severity(line) == expected


def test_event_count_is_capped():
    log = "\n".join(f"ERROR unique failure type {'x' * i}" for i in range(MAX_EVENTS + 50))
    assert len(extract_error_events(log)) == MAX_EVENTS


def test_message_is_truncated():
    log = "ERROR " + "x" * (MAX_MESSAGE_CHARS + 200)
    assert len(extract_error_events(log)[0].message) == MAX_MESSAGE_CHARS