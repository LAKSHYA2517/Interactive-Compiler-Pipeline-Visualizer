from backend.common.ids import IdGen
from backend.common.span import line_starts, make_span, merge


def test_span_merge_and_lines():
    src = "ab\ncd"
    st = line_starts(src)
    a, b = make_span(st, 0, 2), make_span(st, 3, 5)
    m = merge([b, a])
    assert (m.start, m.end, m.line, m.col, m.end_line, m.end_col) == (0, 5, 1, 1, 2, 3)


def test_ids_deterministic():
    g = IdGen()
    assert [g.next("tok"), g.next("tok"), g.next("ast")] == ["tok_0", "tok_1", "ast_0"]
