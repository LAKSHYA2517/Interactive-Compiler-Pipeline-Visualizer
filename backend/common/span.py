"""Source spans. Offsets are 0-based, end-exclusive; line/col are 1-based."""
from pydantic import BaseModel


class Span(BaseModel):
    start: int
    end: int
    line: int
    col: int
    end_line: int
    end_col: int


def merge(spans: list[Span]) -> Span:
    """Smallest span covering all of `spans` (must be non-empty)."""
    first = min(spans, key=lambda s: s.start)
    last = max(spans, key=lambda s: s.end)
    return Span(start=first.start, end=last.end, line=first.line, col=first.col,
                end_line=last.end_line, end_col=last.end_col)


def line_starts(source: str) -> list[int]:
    out = [0]
    for i, ch in enumerate(source):
        if ch == "\n":
            out.append(i + 1)
    return out


def make_span(starts: list[int], start: int, end: int) -> Span:
    """Build a Span from offsets using precomputed line starts."""
    import bisect
    l1 = bisect.bisect_right(starts, start) - 1
    l2 = bisect.bisect_right(starts, end) - 1 if end > start else l1
    return Span(start=start, end=end, line=l1 + 1, col=start - starts[l1] + 1,
                end_line=l2 + 1, end_col=end - starts[l2] + 1)
