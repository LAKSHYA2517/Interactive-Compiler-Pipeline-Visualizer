"""Hand-written character-by-character scanner.

Concept: lexical analysis, longest match, keyword lookup after identifier scan.
"""
from pydantic import BaseModel

from ..common.diagnostics import Diagnostic
from ..common.explain import explain
from ..common.ids import IdGen
from ..common.span import Span, line_starts, make_span
from ..parser.rules import RULES

KEYWORDS = {"int", "float", "bool", "if", "else", "while", "print", "true", "false"}
TWO_CHAR_OPS = {"==", "!=", "<=", ">=", "&&", "||"}
ONE_CHAR_OPS = set("+-*/=<>!")
DELIMS = set("(){};")


class Token(BaseModel):
    id: str
    type: str
    lexeme: str
    span: Span
    origin: list[str] = []


class LexResult(BaseModel):
    tokens: list[Token]
    diagnostics: list[Diagnostic]


def tokenize(source: str, ids: IdGen | None = None) -> LexResult:
    ids = ids or IdGen()
    st = line_starts(source)
    toks: list[Token] = []
    diags: list[Diagnostic] = []
    n, i = len(source), 0

    def emit(kind: str, a: int, b: int) -> None:
        toks.append(Token(id=ids.next("tok"), type=kind, lexeme=source[a:b], span=make_span(st, a, b)))

    while i < n:
        c = source[i]
        if c in " \t\r\n":
            i += 1
        elif source.startswith("//", i):
            while i < n and source[i] != "\n":
                i += 1
        elif c.isascii() and (c.isalpha() or c == "_"):
            j = i + 1
            while j < n and source[j].isascii() and (source[j].isalnum() or source[j] == "_"):
                j += 1
            emit("KEYWORD" if source[i:j] in KEYWORDS else "IDENTIFIER", i, j)
            i = j
        elif c.isascii() and c.isdigit():
            j = i + 1
            while j < n and source[j].isdigit():
                j += 1
            if j + 1 < n and source[j] == "." and source[j + 1].isdigit():
                j += 1
                while j < n and source[j].isdigit():
                    j += 1
                emit("FLOAT_LIT", i, j)
            else:
                emit("INT_LIT", i, j)
            i = j
        elif source[i:i + 2] in TWO_CHAR_OPS:
            emit("OPERATOR", i, i + 2)
            i += 2
        elif c in ONE_CHAR_OPS:
            emit("OPERATOR", i, i + 1)
            i += 1
        elif c in DELIMS:
            emit("DELIMITER", i, i + 1)
            i += 1
        else:
            sp = make_span(st, i, i + 1)
            did = ids.next("diag")
            diags.append(Diagnostic(
                id=did, severity="error", phase="lexer", message=f"Unknown character '{c}'.", span=sp, origin=[],
                explanation=explain(RULES, "LEX_UNKNOWN_CHAR", [], sp, ch=c)))
            i += 1
    toks.append(Token(id=ids.next("tok"), type="EOF", lexeme="", span=make_span(st, n, n)))
    return LexResult(tokens=toks, diagnostics=diags)
