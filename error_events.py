"""Rule-based extraction of structured error events from raw log text.

No LLM and no I/O: a string goes in, a list of ErrorEvent comes out. These map
one-to-one onto rows of the error_events table (minus analysis_id).
"""
import re
from dataclasses import dataclass

from log_parser import ERROR_PATTERN

MAX_EVENTS = 100          # keep at most this many distinct events per analysis
MAX_MESSAGE_CHARS = 500   # truncate stored message text

# Severity levels, most severe first. Lines with no level get None.
SEVERITY_ORDER = ("FATAL", "CRITICAL", "ERROR")
SEVERITY_PATTERN = re.compile(r"\b(FATAL|CRITICAL|ERROR)\b", re.IGNORECASE)

# Category rules. ORDER MATTERS: the first rule that matches wins.
CATEGORY_RULES = [
    ("timeout", r"timeout|timed out"),
    ("connection", r"connection (?:refused|reset|closed|failed)|could not connect|unable to connect|reset by peer"),
    ("database", r"deadlock|\bsql\b|constraint|query failed"),
    ("memory", r"out of memory|\boom\b|memoryerror"),
    ("auth", r"unauthori[sz]ed|forbidden|invalid token|permission denied"),
    ("crash", r"segfault|segmentation fault|fatal|traceback|uncaught exception"),
]
CATEGORY_RULES = [(name, re.compile(p, re.IGNORECASE)) for name, p in CATEGORY_RULES]
DEFAULT_CATEGORY = "other"

# Used to normalize lines so the same error at different times groups together.
_TIMESTAMP = re.compile(
    r"\d{4}-\d{2}-\d{2}[T ]\d{2}:\d{2}:\d{2}(?:[.,]\d+)?(?:Z|[+-]\d{2}:?\d{2})?"
)
_CLOCK = re.compile(r"\b\d{2}:\d{2}:\d{2}(?:[.,]\d+)?\b")
_HEX = re.compile(r"\b0x[0-9a-f]+\b", re.IGNORECASE)
_NUMBER = re.compile(r"\d+")
_SPACES = re.compile(r"\s+")


@dataclass(frozen=True)
class ErrorEvent:
    severity: str | None
    category: str
    message: str
    repeat_count: int


def normalize_message(line: str) -> str:
    """Grouping key: strip timestamps, hex values and numbers, collapse spaces."""
    s = _TIMESTAMP.sub(" ", line)
    s = _CLOCK.sub(" ", s)
    s = _HEX.sub("N", s)
    s = _NUMBER.sub("N", s)
    return _SPACES.sub(" ", s).strip().lower()


def detect_severity(line: str) -> str | None:
    found = {m.upper() for m in SEVERITY_PATTERN.findall(line)}
    for level in SEVERITY_ORDER:
        if level in found:
            return level
    return None


def detect_category(line: str) -> str:
    for name, pattern in CATEGORY_RULES:
        if pattern.search(line):
            return name
    return DEFAULT_CATEGORY


def extract_error_events(raw_text: str) -> list[ErrorEvent]:
    """Return distinct error events with repeat counts, most frequent first.

    Pass the RAW log text (not the output of collapse_repeats), so counts are real.
    """
    groups: dict[str, dict] = {}  # insertion-ordered: first appearance wins ties
    for line in raw_text.splitlines():
        if not ERROR_PATTERN.search(line):
            continue
        key = normalize_message(line)
        if key in groups:
            groups[key]["count"] += 1
        else:
            groups[key] = {"line": line.strip(), "count": 1}

    events = [
        ErrorEvent(
            severity=detect_severity(g["line"]),
            category=detect_category(g["line"]),
            message=g["line"][:MAX_MESSAGE_CHARS],
            repeat_count=g["count"],
        )
        for g in groups.values()
    ]
    events.sort(key=lambda e: -e.repeat_count)  # stable sort keeps first-seen order on ties
    return events[:MAX_EVENTS]