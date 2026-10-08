import pytest

from .helpers import front


def rules(src):
    _, ps, sm = front(src)
    return [d.explanation.rule_id for d in ps.diagnostics + sm.diagnostics]


def test_lexer_basics():
    lx, _, _ = front("int a = 1.5; // c\n a == 2 && x_1 >= 3 $")
    assert [t.type for t in lx.tokens][:5] == ["KEYWORD", "IDENTIFIER", "OPERATOR", "FLOAT_LIT", "DELIMITER"]
    assert "==" in [t.lexeme for t in lx.tokens] and ">=" in [t.lexeme for t in lx.tokens]
    assert lx.diagnostics[0].explanation.rule_id == "LEX_UNKNOWN_CHAR"
    assert lx.tokens[-1].type == "EOF"


def test_precedence_and_assoc():
    _, ps, _ = front("int a = 1 - 2 - 3 * 4;")
    e = ps.ast.children[0].children[0]
    assert e.operator == "-" and e.children[0].operator == "-" and e.children[1].operator == "*"


def test_syntax_recovery():
    _, ps, _ = front("int a = ; int b = 2; int c = ; print(b);")
    assert len(ps.diagnostics) == 2
    assert ps.diagnostics[0].explanation.detail["expected"] == ["expression"]
    assert [c.kind for c in ps.ast.children] == ["Decl", "Print"]


def test_missing_semicolon():
    assert rules("int a = 1 int b = 2;") == ["SYN_MISSING_SEMICOLON"]


@pytest.mark.parametrize("src,rule", [
    ("int a; b = 10;", "SEM_UNDECLARED"),
    ("int a; a = 10.5;", "SEM_TYPE_MISMATCH"),
    ("int a = 1; int a = 2;", "SEM_REDECLARED"),
    ("int x = 5; if (x) { x = 1; }", "SEM_COND_NOT_BOOL"),
    ("int a = 1; bool b = a && true;", "SEM_BAD_OPERAND"),
    ("int a; print(a);", "SEM_UNINIT_USE"),
])
def test_semantic_rules(src, rule):
    assert rules(src) == [rule]


def test_messages_and_shadowing():
    _, _, sm = front("int a; b = 10;")
    assert sm.diagnostics[0].message == "Variable 'b' is not declared."
    assert sm.diagnostics[0].span.start == 7
    _, _, sm = front("int a = 1; { int a = 2; a = a + 1; } a = 3;")
    assert not sm.diagnostics and [s.scope for s in sm.symbols] == ["global", "block_1"]
    assert [s.tac_name for s in sm.symbols] == ["a", "a_block_1"]
