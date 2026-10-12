"""Pydantic models: single source of truth for the API contract."""
from typing import Optional

from pydantic import BaseModel

from ..common.diagnostics import Diagnostic
from ..codegen.asm_gen import AsmLine
from ..ir.tac import Instr
from ..lexer.dfa import DfaResult
from ..lexer.tokenizer import Token
from ..optimizer.passes import Applied
from ..parser.ast import AstNode
from ..parser.slr_parser import SlrRun
from ..parser.slr_table import SlrTable
from ..semantic.symbol_table import Symbol


class SourceReq(BaseModel):
    source: str


class CompileReq(BaseModel):
    source: str
    optimize: bool = False
    passes: Optional[list[str]] = None


class OptimizeReq(BaseModel):
    source: str
    passes: Optional[list[str]] = None


class DfaReq(BaseModel):
    regex: str
    test_input: Optional[str] = None


class GrammarReq(BaseModel):
    grammar_text: str
    test_input: Optional[str] = None


class Optimized(BaseModel):
    tac: list[Instr]
    applied: list[Applied]


class PhaseStatus(BaseModel):
    lexer: str = "skipped"     # ok | failed | skipped
    parser: str = "skipped"
    semantic: str = "skipped"
    ir: str = "skipped"
    optimizer: str = "skipped"
    codegen: str = "skipped"


class CompileResponse(BaseModel):
    ok: bool
    source: str
    tokens: Optional[list[Token]] = None
    ast: Optional[AstNode] = None
    symbols: Optional[list[Symbol]] = None
    diagnostics: list[Diagnostic] = []
    tac: Optional[list[Instr]] = None
    optimized: Optional[Optimized] = None
    asm: Optional[list[AsmLine]] = None          # assembly for optimized TAC if present, else plain TAC
    asm_from: Optional[str] = None               # "optimized" | "tac"
    phases: PhaseStatus = PhaseStatus()


class TokenizeResponse(BaseModel):
    tokens: list[Token]
    diagnostics: list[Diagnostic]


class ParseResponse(BaseModel):
    ast: Optional[AstNode]
    diagnostics: list[Diagnostic]
    table: Optional[SlrTable] = None   # tier 2: SLR(1) table for the MiniLang grammar
    slr: Optional[SlrRun] = None       # tier 2: trace + concrete parse tree


class GrammarResponse(BaseModel):
    first: dict[str, list[str]]
    follow: dict[str, list[str]]
    table: SlrTable
    conflicts: list
    run: Optional[SlrRun] = None


class SemanticResponse(BaseModel):
    symbols: Optional[list[Symbol]]
    diagnostics: list[Diagnostic]
    ast: Optional[AstNode]


class IrResponse(BaseModel):
    tac: Optional[list[Instr]]
    diagnostics: list[Diagnostic] = []


class OptimizeResponse(BaseModel):
    before: Optional[list[Instr]]
    after: Optional[list[Instr]]
    applied: list[Applied] = []
    diagnostics: list[Diagnostic] = []


DfaResponse = DfaResult
