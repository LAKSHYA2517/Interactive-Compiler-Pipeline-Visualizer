"""Three-address code quadruples. Concept: intermediate representation."""
import re
from typing import Literal, Optional

from pydantic import BaseModel, computed_field

from ..common.span import Span

Op = Literal["binop", "unop", "copy", "label", "goto", "if_goto", "print"]
LITERAL = re.compile(r"^(-?\d+(\.\d+)?|true|false)$")
TEMP = re.compile(r"^t\d+$")


def is_lit(x: Optional[str]) -> bool:
    return x is not None and bool(LITERAL.match(x))


def is_temp(x: Optional[str]) -> bool:
    return x is not None and bool(TEMP.match(x))


class Instr(BaseModel):
    id: str
    op: Op
    dest: Optional[str] = None      # binop/unop/copy target
    a: Optional[str] = None         # first operand (or condition/print operand)
    b: Optional[str] = None         # second operand
    operator: Optional[str] = None  # binop/unop operator; if_goto relop
    label: Optional[str] = None     # label / goto / if_goto target
    ty: Optional[str] = None        # result type of binop/unop (int, float, bool)
    span: Span
    origin: list[str]

    @computed_field
    @property
    def text(self) -> str:
        o = self.op
        if o == "copy":
            return f"{self.dest} = {self.a}"
        if o == "binop":
            return f"{self.dest} = {self.a} {self.operator} {self.b}"
        if o == "unop":
            return f"{self.dest} = {self.operator}{self.a}"
        if o == "label":
            return f"{self.label}:"
        if o == "goto":
            return f"goto {self.label}"
        if o == "if_goto":
            cond = self.a if self.operator is None else f"{self.a} {self.operator} {self.b}"
            return f"if {cond} goto {self.label}"
        return f"print {self.a}"

    def reads(self) -> list[str]:
        if self.op in ("label", "goto"):
            return []
        return [x for x in (self.a, self.b) if x is not None and not is_lit(x)]
