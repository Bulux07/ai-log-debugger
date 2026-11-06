import re

#common software failure keywords
ERROR_PATTERN = re.compile(
    r"error|exception|traceback|fatal|critical|failed|timeout|segfault|deadlock",
    re.IGNORECASE,
)

#prevents program from crashing 
def read_log(path):
    with open(path, "r", encoding="utf-8", errors="replace") as f:
        return f.read().splitlines()

#prevents same log being printed multiple times
def collapse_repeats(lines):
    """Collapse consecutive identical lines into one line with a repeat count."""
    out, prev, count = [], None, 0
    for line in lines:
        if line == prev:
            count += 1
            continue
        if prev is not None:
            out.append(prev if count == 1 else f"{prev}  [repeated {count}x]")
        prev, count = line, 1
    if prev is not None:
        out.append(prev if count == 1 else f"{prev}  [repeated {count}x]")
    return out

#It grabs the error line plus 3 lines before and after.
#This ensures AI gets crucial stack trace context
def select_relevant(lines, context=3):
    """Keep error-like lines plus a few lines of context around each."""
    keep = set()
    for i, line in enumerate(lines):
        if ERROR_PATTERN.search(line):
            keep.update(range(max(0, i - context), min(len(lines), i + context + 1)))
    return [lines[i] for i in sorted(keep)]

def parse_log(path, max_chars=400_000):
    lines = collapse_repeats(read_log(path))
    relevant = select_relevant(lines)
    selected = relevant if relevant else lines    # no keywords found: use everything
    text = "\n".join(selected)
    if len(text) > max_chars:
        text = text[-max_chars:]    # keep the end, where recent errors usually are
    return text