"""TAC -> assembly for a small register machine (R1/R2 scratch, variables and temporaries in memory).

Concept: code generation. Naive strategy: every TAC instruction loads its operands into registers,
computes, and stores the result back, so no register allocation is needed. Types come from the
symbol table (temporaries included) so int/float instructions and ITOF conversions are chosen correctly.

ISA: MOV Rd,imm | LD Rd,var | ST var,Rs | ADD/SUB/MUL/DIV Rd,Ra,Rb (F-prefixed for float) |
SLT SLE SGT SGE SEQ SNE Rd,Ra,Rb (F-prefixed for float) | AND OR Rd,Ra,Rb | NEG/NOT Rd,Rs | ITOF Rd,Rs |
BEQ BNE BLT BLE BGT BGE Ra,Rb,L | BNZ Rs,L | JMP L | PRINT Rs | HALT
"""
from typing import Optional

from pydantic import BaseModel

from ..common.ids import IdGen
from ..common.span import Span
from ..ir.tac import Instr, is_lit
from ..semantic.symbol_table import Symbol

ARITH = {"+": "ADD", "-": "SUB", "*": "MUL", "/": "DIV"}
SET = {"<": "SLT", "<=": "SLE", ">": "SGT", ">=": "SGE", "==": "SEQ", "!=": "SNE"}
BRANCH = {"<": "BLT", "<=": "BLE", ">": "BGT", ">=": "BGE", "==": "BEQ", "!=": "BNE"}
LOGIC = {"&&": "AND", "||": "OR"}


class AsmLine(BaseModel):
    id: str
    kind: str                 # directive | label | instr
    text: str                 # the assembly (no comment)
    comment: str = ""         # the TAC line (or variable) it came from
    span: Span
    origin: list[str]         # TAC instruction id, or symbol id for data lines


class Gen:
    def __init__(self, symbols: list[Symbol], ids: IdGen):
        self.sym = {s.tac_name: s for s in symbols}
        self.ids, self.out = ids, []

    def ty(self, x: str) -> str:
        if x in ("true", "false"):
            return "bool"
        if is_lit(x):
            return "float" if "." in x else "int"
        return self.sym[x].type

    def add(self, kind: str, text: str, comment: str, span: Span, origin: list[str]) -> None:
        self.out.append(AsmLine(id=self.ids.next("asm"), kind=kind, text=text, comment=comment, span=span, origin=origin))

    def load(self, reg: str, x: str, floaty: bool, i: Instr) -> None:
        """Load operand x into reg, converting int to float when the operation is a float one."""
        if is_lit(x):
            v = {"true": "1", "false": "0"}.get(x, x)
            if floaty and self.ty(x) != "float":
                v += ".0"
            self.emit(f"MOV {reg}, {v}", i)
            return
        self.emit(f"LD {reg}, {x}", i)
        if floaty and self.ty(x) != "float":
            self.emit(f"ITOF {reg}, {reg}", i)

    def emit(self, text: str, i: Instr) -> None:
        self.add("instr", text, "", i.span, [i.id])

    def instr(self, i: Instr) -> None:
        start = len(self.out)
        o = i.op
        if o == "label":
            self.add("label", f"{i.label}:", i.text, i.span, [i.id])
        elif o == "goto":
            self.emit(f"JMP {i.label}", i)
        elif o == "copy":
            self.load("R1", i.a, self.sym_ty(i.dest) == "float", i)
            self.emit(f"ST {i.dest}, R1", i)
        elif o == "unop":
            f = self.ty(i.a) == "float"
            self.load("R1", i.a, False, i)
            self.emit(("FNEG" if f else "NEG") + " R1, R1" if i.operator == "-" else "NOT R1, R1", i)
            self.emit(f"ST {i.dest}, R1", i)
        elif o == "binop":
            f = "float" in (self.ty(i.a), self.ty(i.b))
            self.load("R1", i.a, f, i)
            self.load("R2", i.b, f, i)
            op = i.operator
            m = LOGIC.get(op) or ((("F" if f else "") + ARITH[op]) if op in ARITH else ("F" if f else "") + SET[op])
            self.emit(f"{m} R1, R1, R2", i)
            self.emit(f"ST {i.dest}, R1", i)
        elif o == "if_goto":
            if i.operator is None:
                self.load("R1", i.a, False, i)
                self.emit(f"BNZ R1, {i.label}", i)
            else:
                f = "float" in (self.ty(i.a), self.ty(i.b))
                self.load("R1", i.a, f, i)
                self.load("R2", i.b, f, i)
                if f:   # float compare sets R1, then branch on it
                    self.emit(f"F{SET[i.operator]} R1, R1, R2", i)
                    self.emit(f"BNZ R1, {i.label}", i)
                else:
                    self.emit(f"{BRANCH[i.operator]} R1, R2, {i.label}", i)
        elif o == "print":
            self.load("R1", i.a, False, i)
            self.emit("PRINT R1", i)
        if o != "label" and len(self.out) > start:
            self.out[start].comment = i.text

    def sym_ty(self, name: str) -> str:
        return self.sym[name].type


def generate_asm(tac: list[Instr], symbols: list[Symbol], ids: IdGen | None = None) -> list[AsmLine]:
    g = Gen(symbols, ids or IdGen())
    used = {x for i in tac for x in [i.dest, *i.reads()] if x and not is_lit(x)}
    first = tac[0].span if tac else None
    for s in symbols:
        if s.tac_name in used:
            g.add("directive", f"{s.tac_name}: {'.float' if s.type == 'float' else '.word'} 0",
                  f"{s.type} {s.name}" if s.kind == "variable" else f"{s.type} temporary", s.span, [s.id])
    # section markers carry the first symbol/instruction's span
    data_span = g.out[0].span if g.out else first
    out_head = []
    if data_span:
        out_head.append(AsmLine(id="", kind="directive", text=".data", span=data_span, origin=g.out[0].origin if g.out else []))
    g.out = out_head + g.out
    if tac:
        g.add("directive", ".text", "", tac[0].span, [tac[0].id])
    for i in tac:
        g.instr(i)
    if tac:
        g.add("instr", "HALT", "", tac[-1].span, [tac[-1].id])
    for k, line in enumerate(g.out):   # renumber so ids are dense and deterministic
        line.id = f"asm_{k}"
    return g.out
