from functools import lru_cache

from fastapi import APIRouter, HTTPException

from ..lexer.dfa import build
from ..lexer.tokenizer import tokenize
from ..parser.grammar import MINILANG, parse_grammar
from ..parser.slr_parser import run as slr_run
from ..parser.slr_table import build_table
from .pipeline import compile_source
from .schemas import (CompileReq, CompileResponse, DfaReq, DfaResponse, GrammarReq, IrResponse, OptimizeReq,
                      GrammarResponse, OptimizeResponse, ParseResponse, SemanticResponse, SourceReq, TokenizeResponse)

router = APIRouter()


@lru_cache
def minilang_slr():
    g = parse_grammar(MINILANG)
    return g, build_table(g)


@router.get("/health")
def health():
    return {"status": "ok"}


@router.post("/compile", response_model=CompileResponse)
def compile_(req: CompileReq):
    return compile_source(req.source, req.optimize, req.passes)


@router.post("/tokenize", response_model=TokenizeResponse)
def tokenize_(req: SourceReq):
    return tokenize(req.source)


@router.post("/build-dfa", response_model=DfaResponse)
def build_dfa(req: DfaReq):
    try:
        return build(req.regex, req.test_input)
    except (ValueError, IndexError) as e:
        raise HTTPException(422, str(e) if isinstance(e, ValueError) else "Malformed regex")


@router.post("/parse", response_model=ParseResponse)
def parse_(req: SourceReq):
    from ..parser.slr_parser import terminal_of
    r = compile_source(req.source, until="parser")
    g, table = minilang_slr()
    toks = [(terminal_of(t), t.lexeme, t.id) for t in r.tokens]
    return ParseResponse(ast=r.ast, diagnostics=r.diagnostics, table=table, slr=slr_run(g, table, toks))


@router.post("/semantic-analysis", response_model=SemanticResponse)
def semantic(req: SourceReq):
    r = compile_source(req.source, until="semantic")
    return SemanticResponse(symbols=r.symbols, diagnostics=r.diagnostics, ast=r.ast)


@router.post("/generate-ir", response_model=IrResponse)
def ir(req: SourceReq):
    r = compile_source(req.source, until="ir")
    return IrResponse(tac=r.tac, diagnostics=r.diagnostics)


@router.post("/optimize", response_model=OptimizeResponse)
def optimize_(req: OptimizeReq):
    r = compile_source(req.source, True, req.passes)
    o = r.optimized
    return OptimizeResponse(before=r.tac, after=o.tac if o else None, applied=o.applied if o else [],
                            diagnostics=r.diagnostics)


@router.post("/grammar/analyze", response_model=GrammarResponse)
def grammar_analyze(req: GrammarReq):
    try:
        g = parse_grammar(req.grammar_text)
    except ValueError as e:
        raise HTTPException(422, str(e))
    t = build_table(g)
    toks = None
    if req.test_input is not None:
        toks = [(w, w, None) for w in req.test_input.split()] + [("$", "", None)]
    return GrammarResponse(first=t.first, follow=t.follow, table=t, conflicts=t.conflicts,
                           run=slr_run(g, t, toks) if toks else None)
