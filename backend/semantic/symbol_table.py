"""Symbol table with a scope stack. Concept: scopes, declaration/use binding."""
from pydantic import BaseModel

from ..common.ids import symbol_id


class Symbol(BaseModel):
    id: str
    name: str
    type: str
    scope: str
    decl: str            # declaring AST node id
    uses: list[str] = []  # AST node ids that read or write it
    initialized: bool = False
    tac_name: str        # name used in IR (disambiguated when shadowing)
    span: "Span"         # declaration identifier
    origin: list[str]
    kind: str = "variable"   # variable | temp (IR temporaries are appended after TAC generation)


from ..common.span import Span  # noqa: E402

Symbol.model_rebuild()


class ScopeStack:
    def __init__(self) -> None:
        self.stack: list[tuple[str, dict[str, Symbol]]] = [("global", {})]
        self.count = 0
        self.symbols: list[Symbol] = []

    @property
    def current(self) -> str:
        return self.stack[-1][0]

    def push(self) -> None:
        self.count += 1
        self.stack.append((f"block_{self.count}", {}))

    def pop(self) -> None:
        self.stack.pop()

    def lookup(self, name: str) -> Symbol | None:
        for _, table in reversed(self.stack):
            if name in table:
                return table[name]
        return None

    def local(self, name: str) -> Symbol | None:
        return self.stack[-1][1].get(name)

    def visible_scopes(self) -> str:
        return " > ".join(s for s, _ in reversed(self.stack))

    def declare(self, name: str, ty: str, decl: str, span: Span, origin: list[str], init: bool) -> Symbol:
        taken = any(s.name == name for s in self.symbols)
        scope = self.current
        sym = Symbol(id=symbol_id(name, scope), name=name, type=ty, scope=scope, decl=decl, initialized=init,
                     tac_name=f"{name}_{scope}" if taken else name, span=span, origin=origin)
        self.stack[-1][1][name] = sym
        self.symbols.append(sym)
        return sym


def temp_symbols(tac: list) -> list[Symbol]:
    """One symbol per TAC temporary: decl = defining instruction, uses = instructions that read it."""
    out: dict[str, Symbol] = {}
    for i in tac:
        if i.dest and i.op in ("binop", "unop") and i.dest not in out:
            out[i.dest] = Symbol(id=symbol_id(i.dest, "temp"), name=i.dest, type=i.ty or "int", scope="temp",
                                 decl=i.id, uses=[], initialized=True, tac_name=i.dest, span=i.span,
                                 origin=[i.id], kind="temp")
    for i in tac:
        for r in i.reads():
            if r in out:
                out[r].uses.append(i.id)
    return list(out.values())
