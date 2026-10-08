"""Recursive-descent parser, one-token lookahead, panic-mode recovery.

Concept: top-down parsing of an LL(1) grammar (left recursion turned into loops).
"""
from pydantic import BaseModel

from ..common.diagnostics import Diagnostic
from ..common.explain import explain
from ..common.ids import IdGen
from ..common.span import Span, merge
from ..lexer.tokenizer import Token
from .ast import AstNode
from .rules import RULES

TYPES = {"int", "float", "bool"}
RELOPS = {"<", "<=", ">", ">=", "==", "!="}
STMT_START = TYPES | {"if", "while", "print", "{"}


class ParseResult(BaseModel):
    ast: AstNode
    diagnostics: list[Diagnostic]


class _Sync(Exception):
    """Raised on a syntax error; caught at statement level for recovery."""


class Parser:
    def __init__(self, tokens: list[Token], ids: IdGen):
        self.t, self.i, self.ids = tokens, 0, ids
        self.diags: list[Diagnostic] = []

    # --- helpers
    @property
    def cur(self) -> Token:
        return self.t[self.i]

    def at(self, lex: str) -> bool:
        return self.cur.type != "EOF" and self.cur.lexeme == lex and self.cur.type in ("KEYWORD", "OPERATOR", "DELIMITER")

    def node(self, kind: str, children: list[AstNode], toks: list[Token], **kw) -> AstNode:
        spans = [c.span for c in children] + [t.span for t in toks]
        return AstNode(id=self.ids.next("ast"), kind=kind, span=merge(spans), origin=[t.id for t in toks],
                       children=children, **kw)

    def advance(self) -> Token:
        t = self.cur
        if t.type != "EOF":
            self.i += 1
        return t

    def error(self, expected: list[str], semicolon: bool = False) -> _Sync:
        found = self.cur
        did = self.ids.next("diag")
        shown = found.lexeme or "end of input"
        exp = ", ".join(f"'{e}'" for e in expected)
        rule = "SYN_MISSING_SEMICOLON" if semicolon else "SYN_UNEXPECTED_TOKEN"
        msg = f"Expected {exp} but found '{shown}'."
        ex = explain(RULES, rule, [found.id], found.span, detail={"expected": expected},
                     expected=exp, found=shown)
        self.diags.append(Diagnostic(id=did, severity="error", phase="parser", message=msg, span=found.span,
                                     origin=[found.id], explanation=ex))
        return _Sync()

    def expect(self, lex: str, semicolon: bool = False) -> Token:
        if self.at(lex):
            return self.advance()
        raise self.error([lex], semicolon)

    def expect_id(self) -> Token:
        if self.cur.type == "IDENTIFIER":
            return self.advance()
        raise self.error(["identifier"])

    # --- statements
    def program(self) -> AstNode:
        stmts = self.stmt_list(top=True)
        eof = self.cur
        if stmts:
            return AstNode(id=self.ids.next("ast"), kind="Program", span=merge([s.span for s in stmts]),
                           origin=[], children=stmts)
        return AstNode(id=self.ids.next("ast"), kind="Program", span=eof.span, origin=[], children=[])

    def stmt_list(self, top: bool) -> list[AstNode]:
        out: list[AstNode] = []
        while self.cur.type != "EOF" and not (not top and self.at("}")):
            start = self.i
            try:
                out.append(self.stmt())
            except _Sync:
                self.recover(start)
        return out

    def recover(self, start: int) -> None:
        """Panic mode: skip to just past the next ';' (or stop before '}')."""
        while self.cur.type != "EOF" and not self.at("}"):
            if self.advance().lexeme == ";":
                break
        if self.i == start and self.cur.type != "EOF":
            self.advance()  # guarantee progress

    def stmt(self) -> AstNode:
        c = self.cur
        if c.type == "KEYWORD" and c.lexeme in TYPES:
            return self.decl()
        if c.type == "IDENTIFIER":
            return self.assign()
        if self.at("if"):
            return self.if_stmt()
        if self.at("while"):
            return self.while_stmt()
        if self.at("print"):
            return self.print_stmt()
        if self.at("{"):
            return self.block()
        raise self.error(["type", "identifier", "if", "while", "print", "{"])

    def decl(self) -> AstNode:
        ty = self.advance()
        name = self.expect_id()
        kids: list[AstNode] = []
        toks = [ty, name]
        if self.at("="):
            toks.append(self.advance())
            kids.append(self.expr())
        toks.append(self.expect(";", semicolon=True))
        return self.node("Decl", kids, toks, var_type=ty.lexeme, name=name.lexeme)

    def assign(self) -> AstNode:
        name = self.advance()
        eq = self.expect("=")
        e = self.expr()
        semi = self.expect(";", semicolon=True)
        return self.node("Assign", [e], [name, eq, semi], name=name.lexeme)

    def cond(self) -> tuple[list[Token], AstNode, Token]:
        kw = self.advance()
        lp = self.expect("(")
        e = self.expr()
        rp = self.expect(")")
        return [kw, lp], e, rp

    def if_stmt(self) -> AstNode:
        head, e, rp = self.cond()
        kids, toks = [e, self.block()], head + [rp]
        if self.at("else"):
            toks.append(self.advance())
            kids.append(self.block())
        return self.node("If", kids, toks)

    def while_stmt(self) -> AstNode:
        head, e, rp = self.cond()
        return self.node("While", [e, self.block()], head + [rp])

    def print_stmt(self) -> AstNode:
        kw = self.advance()
        lp = self.expect("(")
        e = self.expr()
        rp = self.expect(")")
        semi = self.expect(";", semicolon=True)
        return self.node("Print", [e], [kw, lp, rp, semi])

    def block(self) -> AstNode:
        lb = self.expect("{")
        stmts = self.stmt_list(top=False)
        rb = self.expect("}")
        return self.node("Block", stmts, [lb, rb])

    # --- expressions (one method per grammar level)
    def binary_level(self, ops: set[str], sub) -> AstNode:
        left = sub()
        while self.cur.type == "OPERATOR" and self.cur.lexeme in ops:
            op = self.advance()
            right = sub()
            left = self.node("Binary", [left, right], [op], operator=op.lexeme)
        return left

    def expr(self) -> AstNode:
        return self.binary_level({"||"}, self.and_e)

    def and_e(self) -> AstNode:
        return self.binary_level({"&&"}, self.rel)

    def rel(self) -> AstNode:
        left = self.add()
        if self.cur.type == "OPERATOR" and self.cur.lexeme in RELOPS:
            op = self.advance()
            right = self.add()
            return self.node("Binary", [left, right], [op], operator=op.lexeme)
        return left

    def add(self) -> AstNode:
        return self.binary_level({"+", "-"}, self.term)

    def term(self) -> AstNode:
        return self.binary_level({"*", "/"}, self.unary)

    def unary(self) -> AstNode:
        if self.cur.type == "OPERATOR" and self.cur.lexeme in ("-", "!"):
            op = self.advance()
            return self.node("Unary", [self.unary()], [op], operator=op.lexeme)
        return self.primary()

    def primary(self) -> AstNode:
        c = self.cur
        if c.type == "INT_LIT":
            self.advance()
            return self.node("Literal", [], [c], value=c.lexeme, lit_type="int")
        if c.type == "FLOAT_LIT":
            self.advance()
            return self.node("Literal", [], [c], value=c.lexeme, lit_type="float")
        if c.type == "KEYWORD" and c.lexeme in ("true", "false"):
            self.advance()
            return self.node("Literal", [], [c], value=c.lexeme, lit_type="bool")
        if c.type == "IDENTIFIER":
            self.advance()
            return self.node("Var", [], [c], name=c.lexeme)
        if self.at("("):
            lp = self.advance()
            e = self.expr()
            rp = self.expect(")")
            # parentheses are transparent in the AST; widen the span to include them
            e = e.model_copy(update={"span": merge([lp.span, e.span, rp.span]), "origin": e.origin + [lp.id, rp.id]})
            return e
        raise self.error(["expression"])


def parse(tokens: list[Token], ids: IdGen | None = None) -> ParseResult:
    p = Parser(tokens, ids or IdGen())
    ast = p.program()
    return ParseResult(ast=ast, diagnostics=p.diags)
