"""One AST walk: scopes, symbol binding, type annotation, diagnostics.

Concept: semantic analysis (symbol table + type checking).
"""
from pydantic import BaseModel

from ..common.diagnostics import Diagnostic
from ..common.explain import explain
from ..common.ids import IdGen
from ..common.span import Span
from ..lexer.tokenizer import Token
from ..parser.ast import AstNode
from .rules import RULES
from .symbol_table import ScopeStack, Symbol

NUMERIC = {"int", "float"}


class SemanticResult(BaseModel):
    symbols: list[Symbol]
    diagnostics: list[Diagnostic]
    ast: AstNode


class Analyzer:
    def __init__(self, tokens: list[Token], ids: IdGen):
        self.tok = {t.id: t for t in tokens}
        self.ids, self.scopes = ids, ScopeStack()
        self.diags: list[Diagnostic] = []

    def report(self, rule: str, node: AstNode, span: Span, message: str, severity="error", **fmt) -> None:
        did = self.ids.next("diag")
        ex = explain(RULES, rule, [node.id], span, **fmt)
        self.diags.append(Diagnostic(id=did, severity=severity, phase="semantic", message=message, span=span,
                                     origin=[node.id], explanation=ex))
        node.error = True

    def name_span(self, n: AstNode, idx: int) -> Span:
        return self.tok[n.origin[idx]].span

    # --- statements
    def stmt(self, n: AstNode) -> None:
        k = n.kind
        if k == "Block":
            self.scopes.push()
            for c in n.children:
                self.stmt(c)
            self.scopes.pop()
        elif k == "Decl":
            rhs = self.expr(n.children[0]) if n.children else None
            nspan = self.name_span(n, 1)
            prev = self.scopes.local(n.name)
            if prev:
                self.report("SEM_REDECLARED", n, nspan,
                            f"'{n.name}' is already declared in this scope (line {prev.span.line}).",
                            name=n.name, scope=self.scopes.current)
                return
            sym = self.scopes.declare(n.name, n.var_type, n.id, nspan, [n.id], bool(n.children))
            n.symbol = sym.id
            if n.children:
                self.check_assign(n, n.var_type, rhs, n.children[0])
        elif k == "Assign":
            rhs = self.expr(n.children[0])
            sym = self.scopes.lookup(n.name)
            if not sym:
                self.undeclared(n, n.name, self.name_span(n, 0))
                return
            n.symbol = sym.id
            sym.uses.append(n.id)
            self.check_assign(n, sym.type, rhs, n.children[0])
            sym.initialized = True
        elif k in ("If", "While"):
            t = self.expr(n.children[0])
            if t is not None and t != "bool":
                self.report("SEM_COND_NOT_BOOL", n.children[0], n.children[0].span,
                            f"Condition must be bool, found {t}.", type=t)
            for c in n.children[1:]:
                self.stmt(c)
        elif k == "Print":
            self.expr(n.children[0])
        else:  # Program
            for c in n.children:
                self.stmt(c)

    def check_assign(self, stmt: AstNode, lhs: str, rhs: str | None, rhs_node: AstNode) -> None:
        if rhs is None or rhs == lhs or (lhs == "float" and rhs == "int"):
            return
        note = "; float to int loses information." if (lhs, rhs) == ("int", "float") else "."
        self.report("SEM_TYPE_MISMATCH", stmt, rhs_node.span, f"Cannot assign {rhs} to {lhs}{note}", lhs=lhs, rhs=rhs)

    def undeclared(self, node: AstNode, name: str, span: Span) -> None:
        self.report("SEM_UNDECLARED", node, span, f"Variable '{name}' is not declared.",
                    name=name, scopes=self.scopes.visible_scopes())

    # --- expressions: returns type or None (unknown; suppresses cascades)
    def expr(self, n: AstNode) -> str | None:
        t = self._expr(n)
        n.type = t
        return t

    def _expr(self, n: AstNode) -> str | None:
        if n.kind == "Literal":
            return n.lit_type
        if n.kind == "Var":
            sym = self.scopes.lookup(n.name)
            if not sym:
                self.undeclared(n, n.name, self.tok[n.origin[0]].span)
                return None
            n.symbol = sym.id
            sym.uses.append(n.id)
            if not sym.initialized:
                self.report("SEM_UNINIT_USE", n, n.span, f"'{n.name}' may be used before it is assigned.",
                            severity="warning", name=n.name)
                n.error = False
            return sym.type
        if n.kind == "Unary":
            t = self.expr(n.children[0])
            need = NUMERIC if n.operator == "-" else {"bool"}
            if t is not None and t not in need:
                self.bad(n, n.operator, t, "int or float" if n.operator == "-" else "bool")
                return None
            return t
        # Binary
        a, b = self.expr(n.children[0]), self.expr(n.children[1])
        op = n.operator
        if a is None or b is None:
            return None
        if op in ("+", "-", "*", "/"):
            for t in (a, b):
                if t not in NUMERIC:
                    return self.bad(n, op, t, "int or float")
            return "float" if "float" in (a, b) else "int"
        if op in ("<", "<=", ">", ">="):
            for t in (a, b):
                if t not in NUMERIC:
                    return self.bad(n, op, t, "int or float")
            return "bool"
        if op in ("==", "!="):
            if a == b or (a in NUMERIC and b in NUMERIC):
                return "bool"
            return self.bad(n, op, b, "two numeric or two bool operands")
        for t in (a, b):  # && ||
            if t != "bool":
                return self.bad(n, op, t, "bool")
        return "bool"

    def bad(self, n: AstNode, op: str, t: str, needs: str) -> None:
        self.report("SEM_BAD_OPERAND", n, n.span, f"Operator '{op}' does not accept {t}.", op=op, type=t, needs=needs)
        return None


def analyze(ast: AstNode, tokens: list[Token], ids: IdGen | None = None) -> SemanticResult:
    a = Analyzer(tokens, ids or IdGen())
    a.stmt(ast)
    return SemanticResult(symbols=a.scopes.symbols, diagnostics=a.diags, ast=ast)
