from functools import lru_cache

from backend.lexer.tokenizer import tokenize
from backend.parser.grammar import MINILANG, parse_grammar
from backend.parser.slr_parser import run, terminal_of
from backend.parser.slr_table import build_table


@lru_cache
def mini():
    g = parse_grammar(MINILANG)
    return g, build_table(g)


def test_minilang_conflict_free():
    assert mini()[1].conflicts == []


def test_minilang_parse():
    g, t = mini()
    toks = tokenize("int a = 1 + 2 * 3; while (a < 9) { a = a + 1; } print(a);").tokens
    r = run(g, t, [(terminal_of(x), x.lexeme, x.id) for x in toks])
    assert r.accepted and r.tree.symbol == "program"
    bad = tokenize("int a = ;").tokens
    assert not run(g, t, [(terminal_of(x), x.lexeme, x.id) for x in bad]).accepted


def test_ambiguous_grammar_reports_conflict():
    g = parse_grammar("E -> E + E | id")
    c = build_table(g).conflicts
    assert c and c[0].kind == "shift/reduce" and c[0].symbol == "+"


def test_first_follow_and_epsilon():
    t = build_table(parse_grammar("S -> A b\nA -> a A | ε"))
    assert t.first["A"] == ["a", "ε"] and t.follow["A"] == ["b"]
    assert not t.conflicts
