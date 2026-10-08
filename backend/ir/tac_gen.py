"""AST -> TAC quadruples. Concept: syntax-directed translation, labels for control flow."""
from ..common.ids import IdGen
from ..parser.ast import AstNode
from ..semantic.symbol_table import Symbol
from .tac import Instr

RELOPS = {"<", "<=", ">", ">=", "==", "!="}


class Gen:
    def __init__(self, symbols: list[Symbol], ids: IdGen):
        self.sym = {s.id: s for s in symbols}
        self.ids, self.out = ids, []
        self.ntemp = self.nlabel = 0

    def temp(self) -> str:
        self.ntemp += 1
        return f"t{self.ntemp}"

    def label(self) -> str:
        self.nlabel += 1
        return f"L{self.nlabel}"

    def emit(self, node: AstNode, op: str, **kw) -> None:
        self.out.append(Instr(id=self.ids.next("tac"), op=op, span=node.span, origin=[node.id], **kw))

    def var(self, n: AstNode) -> str:
        return self.sym[n.symbol].tac_name

    def expr(self, n: AstNode) -> str:
        if n.kind == "Literal":
            return n.value
        if n.kind == "Var":
            return self.var(n)
        if n.kind == "Unary":
            a = self.expr(n.children[0])
            t = self.temp()
            self.emit(n, "unop", dest=t, a=a, operator=n.operator, ty=n.type)
            return t
        a, b = self.expr(n.children[0]), self.expr(n.children[1])
        t = self.temp()
        self.emit(n, "binop", dest=t, a=a, b=b, operator=n.operator, ty=n.type)
        return t

    def cond_jump(self, stmt: AstNode, cond: AstNode, target: str) -> None:
        if cond.kind == "Binary" and cond.operator in RELOPS:
            a, b = self.expr(cond.children[0]), self.expr(cond.children[1])
            self.emit(stmt, "if_goto", a=a, b=b, operator=cond.operator, label=target)
        else:
            self.emit(stmt, "if_goto", a=self.expr(cond), label=target)

    def stmt(self, n: AstNode) -> None:
        k = n.kind
        if k in ("Program", "Block"):
            for c in n.children:
                self.stmt(c)
        elif k in ("Decl", "Assign"):
            if n.children:
                v = self.expr(n.children[0])
                self.emit(n, "copy", dest=self.sym[n.symbol].tac_name, a=v)
        elif k == "Print":
            self.emit(n, "print", a=self.expr(n.children[0]))
        elif k == "If":
            has_else = len(n.children) == 3
            l1, l2 = self.label(), self.label()
            l3 = self.label() if has_else else None
            self.cond_jump(n, n.children[0], l1)
            self.emit(n, "goto", label=l2)
            self.emit(n, "label", label=l1)
            self.stmt(n.children[1])
            if has_else:
                self.emit(n, "goto", label=l3)
            self.emit(n, "label", label=l2)
            if has_else:
                self.stmt(n.children[2])
                self.emit(n, "label", label=l3)
        elif k == "While":
            l1, l2, l3 = self.label(), self.label(), self.label()
            self.emit(n, "label", label=l1)
            self.cond_jump(n, n.children[0], l2)
            self.emit(n, "goto", label=l3)
            self.emit(n, "label", label=l2)
            self.stmt(n.children[1])
            self.emit(n, "goto", label=l1)
            self.emit(n, "label", label=l3)


def generate(ast: AstNode, symbols: list[Symbol], ids: IdGen | None = None) -> list[Instr]:
    g = Gen(symbols, ids or IdGen())
    g.stmt(ast)
    return g.out
