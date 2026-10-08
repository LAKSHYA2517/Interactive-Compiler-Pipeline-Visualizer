"""Grammar representation + text parser. Concept: context-free grammars.

Text format: `A -> x y | 'tok' z | ε` per line (alternatives on the same or '|' continuation lines).
Symbols that never appear on a left-hand side are terminals. Quotes are optional.
"""
from pydantic import BaseModel

EPS = "ε"

MINILANG = """
program    -> stmt_list
stmt_list  -> stmt_list stmt | stmt
stmt       -> decl | assign | if_stmt | while_stmt | print_stmt | block
decl       -> type ID ';' | type ID '=' expr ';'
type       -> 'int' | 'float' | 'bool'
assign     -> ID '=' expr ';'
if_stmt    -> 'if' '(' expr ')' block | 'if' '(' expr ')' block 'else' block
while_stmt -> 'while' '(' expr ')' block
print_stmt -> 'print' '(' expr ')' ';'
block      -> '{' stmt_list '}'
expr       -> expr '||' and_e | and_e
and_e      -> and_e '&&' rel | rel
rel        -> add RELOP add | add
add        -> add '+' term | add '-' term | term
term       -> term '*' unary | term '/' unary | unary
unary      -> '-' unary | '!' unary | primary
primary    -> INT_LIT | FLOAT_LIT | 'true' | 'false' | ID | '(' expr ')'
"""


class Grammar(BaseModel):
    start: str
    productions: list[tuple[str, tuple[str, ...]]]   # index 0 is the augmented S' -> S
    nonterminals: list[str]
    terminals: list[str]


def parse_grammar(text: str) -> Grammar:
    rules: list[tuple[str, list[list[str]]]] = []
    for raw in text.strip().splitlines():
        line = raw.split("#")[0].strip()
        if not line:
            continue
        if line.startswith("|") and rules:
            rules[-1][1].extend(_alts(line[1:]))
            continue
        if "->" not in line:
            raise ValueError(f"Line has no '->': {raw!r}")
        lhs, rhs = (x.strip() for x in line.split("->", 1))
        if not lhs or " " in lhs:
            raise ValueError(f"Bad left-hand side: {lhs!r}")
        rules.append((lhs, _alts(rhs)))
    if not rules:
        raise ValueError("Empty grammar")
    nts = list(dict.fromkeys(l for l, _ in rules))
    start = rules[0][0]
    prods: list[tuple[str, tuple[str, ...]]] = [(start + "'", (start,))]
    for lhs, alts in rules:
        prods += [(lhs, tuple(a)) for a in alts]
    terms = list(dict.fromkeys(s for _, r in prods for s in r if s not in nts))
    return Grammar(start=start + "'", productions=prods, nonterminals=[start + "'"] + nts, terminals=terms)


def _alts(rhs: str) -> list[list[str]]:
    out = []
    for alt in _split_bar(rhs):
        syms = [s.strip("'") if len(s) > 1 else s for s in alt.split()]
        out.append([] if syms in ([], [EPS], ["epsilon"]) else syms)
    return out


def _split_bar(rhs: str) -> list[str]:
    """Split on '|' that is not the quoted terminal '||'."""
    parts, cur = [], []
    for tok in rhs.split():
        if tok == "|":
            parts.append(" ".join(cur))
            cur = []
        else:
            cur.append(tok)
    parts.append(" ".join(cur))
    return parts
