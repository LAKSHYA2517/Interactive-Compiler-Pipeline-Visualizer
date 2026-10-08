from backend.common.ids import IdGen
from backend.ir.tac_gen import generate
from backend.vm.tac_interpreter import run

from .helpers import front


def tac(src):
    _, ps, sm = front(src)
    assert not sm.diagnostics
    return generate(ps.ast, sm.symbols)


def texts(src):
    return [i.text for i in tac(src)]


def test_demo():
    assert texts("int a = 10; int b = 20; int c = a + b * 2; print(c);") == [
        "a = 10", "b = 20", "t1 = b * 2", "t2 = a + t1", "c = t2", "print c"]


def test_if_else():
    assert texts("int a = 1; int b = 2; int c; if (a < b) { c = a; } else { c = b; }")[2:] == [
        "if a < b goto L1", "goto L2", "L1:", "c = a", "goto L3", "L2:", "c = b", "L3:"]


def test_while():
    assert texts("int i = 0; while (i < 3) { i = i + 1; }")[1:] == [
        "L1:", "if i < 3 goto L2", "goto L3", "L2:", "t1 = i + 1", "i = t1", "goto L1", "L3:"]


def test_run():
    assert run(tac("int i = 0; while (i < 3) { print(i); i = i + 1; } float f = 1; print(f / 2); print(7 / -2);")) == [0, 1, 2, 0.5, -3]
