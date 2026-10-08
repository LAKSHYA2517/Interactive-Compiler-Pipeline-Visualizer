from typing import Optional

from pydantic import BaseModel

from ..common.span import Span


class AstNode(BaseModel):
    id: str
    kind: str  # Program Block Decl Assign If While Print Binary Unary Literal Var
    span: Span
    origin: list[str]
    children: list["AstNode"] = []
    operator: Optional[str] = None
    var_type: Optional[str] = None   # Decl
    name: Optional[str] = None       # Var, Decl, Assign
    value: Optional[str] = None      # Literal (lexeme)
    lit_type: Optional[str] = None   # Literal: int|float|bool
    type: Optional[str] = None       # semantic annotation on expression nodes
    symbol: Optional[str] = None     # Var/Decl/Assign: resolved symbol id
    error: bool = False


def walk(n: AstNode):
    yield n
    for c in n.children:
        yield from walk(c)
