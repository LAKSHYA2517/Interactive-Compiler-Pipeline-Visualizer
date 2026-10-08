import pytest

from backend.lexer.dfa import build

ID = "[a-zA-Z][a-zA-Z0-9]*"


def acc(rx, s):
    return build(rx, s).accepted


def test_identifier():
    assert acc(ID, "Lakshya123") and not acc(ID, "1abc")
    r = build(ID, "Lakshya123")
    assert len(r.steps) == 10 and r.steps[-1].to_state in r.dfa.accept
    assert not build(ID, "a-").steps[-1].to_state


@pytest.mark.parametrize("rx,yes,no", [
    ("(a|b)*abb", ["abb", "babb"], ["ab", ""]),
    ("a+b?", ["a", "aab"], ["b", "abb"]),
    ("[0-9]+(\\.[0-9]+)?", ["12", "1.5"], ["1.", ".5"]),
    ("a[a-c]|[b-d]x", ["ab", "bx", "dx"], ["ax"]),
])
def test_regex(rx, yes, no):
    assert all(acc(rx, s) for s in yes) and not any(acc(rx, s) for s in no)


@pytest.mark.parametrize("bad", ["", "(a", "a)", "[a-", "\\"])
def test_bad(bad):
    with pytest.raises(ValueError):
        build(bad)
