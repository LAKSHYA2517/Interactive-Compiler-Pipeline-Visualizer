"""Composes phase functions. Errors stop the pipeline; warnings do not."""
from ..common.ids import IdGen
from ..ir.tac_gen import generate
from ..lexer.tokenizer import tokenize
from ..optimizer.driver import optimize
from ..parser.ll1_parser import parse
from ..semantic.type_checker import analyze
from .schemas import CompileResponse, Optimized, PhaseStatus


def compile_source(source: str, do_opt: bool = False, passes: list[str] | None = None,
                   until: str = "optimizer") -> CompileResponse:
    order = ["lexer", "parser", "semantic", "ir", "optimizer"]
    ids = IdGen()
    ph = PhaseStatus()
    r = CompileResponse(ok=False, source=source, phases=ph)

    def failed() -> bool:
        return any(d.severity == "error" for d in r.diagnostics)

    def stop(name: str) -> bool:
        return failed() or order.index(name) > order.index(until)

    lx = tokenize(source, ids)
    r.tokens, r.diagnostics = lx.tokens, list(lx.diagnostics)
    ph.lexer = "failed" if failed() else "ok"
    # lexer errors are skipped characters; the parser still runs so more errors can show
    ps = parse(lx.tokens, ids)
    r.ast = ps.ast
    r.diagnostics += ps.diagnostics
    ph.parser = "failed" if ps.diagnostics else "ok"
    if any(d.phase != "lexer" and d.severity == "error" for d in r.diagnostics) or until == "parser":
        return r
    sm = analyze(ps.ast, lx.tokens, ids)
    r.symbols, r.diagnostics = sm.symbols, r.diagnostics + sm.diagnostics
    ph.semantic = "failed" if sm.diagnostics and any(d.severity == "error" for d in sm.diagnostics) else "ok"
    if stop("ir"):
        return r
    r.tac = generate(ps.ast, sm.symbols, ids)
    ph.ir = "ok"
    if do_opt and not stop("optimizer"):
        o = optimize(r.tac, passes, ids)
        r.optimized = Optimized(tac=o.tac, applied=o.applied)
        ph.optimizer = "ok"
    r.ok = not failed()
    return r
