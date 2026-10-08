from backend.common.ids import IdGen
from backend.lexer.tokenizer import tokenize
from backend.parser.ll1_parser import parse
from backend.semantic.type_checker import analyze


def front(src: str):
    ids = IdGen()
    lx = tokenize(src, ids)
    ps = parse(lx.tokens, ids)
    sm = analyze(ps.ast, lx.tokens, ids)
    return lx, ps, sm
