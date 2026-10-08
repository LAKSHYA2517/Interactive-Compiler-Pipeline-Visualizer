import pytest

from backend.ir.tac_gen import generate
from backend.optimizer.driver import optimize
from backend.optimizer.rules import RULES
from backend.vm.tac_interpreter import run

from .helpers import front

DEMO = "int a = 10; int b = 20; int c = a + b * 2; print(c);"


def opt(src, passes=None):
    _, ps, sm = front(src)
    tac = generate(ps.ast, sm.symbols)
    return tac, optimize(tac, passes)


def test_demo_copy_only():
    _, r = opt(DEMO, ["OPT_COPY_PROP"])
    assert [i.text for i in r.tac] == ["a = 10", "b = 20", "t1 = b * 2", "c = a + t1", "print c"]


def test_demo_all():
    _, r = opt(DEMO)
    assert [i.text for i in r.tac] == ["a = 10", "b = 20", "c = 50", "print 50"]
    assert all(a.explanation.rule_id in RULES and a.explanation.origin for a in r.applied)


def test_fold_and_algebraic():
    _, r = opt("int t = 10 * 2; int u = t + 0;")
    rules = {a.rule_id for a in r.applied}
    assert {"OPT_CONST_FOLD", "OPT_ALGEBRAIC"} <= rules


def test_toggle_off():
    _, r = opt(DEMO, ["OPT_CONST_FOLD"])
    assert [i.text for i in r.tac][2] == "t1 = b * 2"


def test_peephole_cse():
    _, r = opt("int a = 3; int b = a * a + a * a; print(b);", ["OPT_CSE"])
    assert any(i.text.endswith("= t1") for i in r.tac)


PROGS = [DEMO,
         "int i = 0; int s = 0; while (i < 5) { s = s + i * 2; i = i + 1; } print(s);",
         "int a = 1; int b = 2; int c; if (a < b) { c = a + 0; } else { c = b * 1; } print(c);",
         "int x = 4; int y = x; x = 7; print(y); print(x * 1); float f = 3; print(f / 2);",
         "bool p = true; if (!p || 1 < 2) { print(1); }"]


@pytest.mark.parametrize("src", PROGS)
@pytest.mark.parametrize("passes", [None, ["OPT_CSE", "OPT_COPY_PROP"], ["OPT_CONST_PROP", "OPT_DEAD_CODE"]])
def test_semantics_preserved(src, passes):
    tac, r = opt(src, passes)
    assert run(tac) == run(r.tac)
