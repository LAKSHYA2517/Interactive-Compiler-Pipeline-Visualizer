import pytest

from backend.api.pipeline import compile_source
from backend.vm.asm_sim import run as asm_run
from backend.vm.tac_interpreter import run as tac_run

from .test_opt import PROGS

FLOATS = ["float f = 1; float g = f / 2 + 0.5; print(g); print(f < g);",
          "int a = 3; float r = a * 1.5; if (r > 4) { print(r); } else { print(0); }",
          "int i = 5; while (i > 0) { i = i - 2; print(-i); }",
          "float x = 2.5; float y = -x; print(y); print(-3);",
          "bool p = true; bool q = false; print(p && !q); print(p || q);"]


def text(r):
    return "\n".join(f"{'' if l.kind != 'instr' else '    '}{l.text}" for l in r.asm)


@pytest.mark.parametrize("src", PROGS + FLOATS)
@pytest.mark.parametrize("opt", [False, True])
def test_asm_matches_tac(src, opt):
    r = compile_source(src, opt)
    want = tac_run(r.optimized.tac if opt else r.tac)
    assert asm_run(text(r)) == want
    assert all(l.origin and l.span.end <= len(src) for l in r.asm)


def test_temps_in_symbol_table_and_demo_asm():
    r = compile_source("int a = 10; int b = 20; int c = a + b * 2; print(c);", False)
    temps = [s for s in r.symbols if s.kind == "temp"]
    assert [(t.name, t.type, len(t.uses)) for t in temps] == [("t1", "int", 1), ("t2", "int", 1)]
    assert temps[0].decl == r.tac[2].id and temps[0].origin
    t = text(r)
    assert "t1: .word 0" in t and "MUL R1, R1, R2" in t and t.rstrip().endswith("HALT")
    assert compile_source("int a = 1;", True).asm_from == "optimized"
