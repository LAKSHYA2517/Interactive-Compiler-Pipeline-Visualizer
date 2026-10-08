"""Table-driven SLR(1) parser: trace + concrete parse tree."""
from pydantic import BaseModel

from ..lexer.tokenizer import Token
from .first_follow import END
from .grammar import Grammar
from .slr_table import SlrTable

RELOPS = {"<", "<=", ">", ">=", "==", "!="}


class TreeNode(BaseModel):
    symbol: str
    lexeme: str | None = None
    token_id: str | None = None
    children: list["TreeNode"] = []


class TraceStep(BaseModel):
    step: int
    stack: str
    input: str
    action: str


class SlrRun(BaseModel):
    trace: list[TraceStep]
    tree: TreeNode | None
    accepted: bool


def terminal_of(t: Token) -> str:
    if t.type == "EOF":
        return END
    if t.type == "IDENTIFIER":
        return "ID"
    if t.type in ("INT_LIT", "FLOAT_LIT"):
        return t.type
    return "RELOP" if t.lexeme in RELOPS else t.lexeme


def run(g: Grammar, table: SlrTable, toks: list[tuple[str, str, str | None]]) -> SlrRun:
    """toks: (terminal, lexeme, token_id); the last must be ('$', '', None)."""
    stack: list[tuple[int, TreeNode | None]] = [(0, None)]
    trace, pos = [], 0
    for step in range(1, 5001):
        st = stack[-1][0]
        term = toks[pos][0]
        act = table.action.get(st, {}).get(term)
        view = " ".join([str(stack[0][0])] + [f"{n.symbol} {s}" for s, n in stack[1:]])
        rest = " ".join(t[0] for t in toks[pos:])
        if act is None:
            trace.append(TraceStep(step=step, stack=view, input=rest, action="error"))
            return SlrRun(trace=trace, tree=None, accepted=False)
        if act == "acc":
            trace.append(TraceStep(step=step, stack=view, input=rest, action="accept"))
            return SlrRun(trace=trace, tree=stack[-1][1], accepted=True)
        if act[0] == "s":
            trace.append(TraceStep(step=step, stack=view, input=rest, action=f"shift {act[1:]}"))
            stack.append((int(act[1:]), TreeNode(symbol=term, lexeme=toks[pos][1], token_id=toks[pos][2])))
            pos += 1
        else:
            p = int(act[1:])
            lhs, rhs = g.productions[p]
            kids = [n for _, n in stack[len(stack) - len(rhs):]] if rhs else []
            del stack[len(stack) - len(rhs):]
            trace.append(TraceStep(step=step, stack=view, input=rest, action=f"reduce {table.productions[p]}"))
            stack.append((table.goto[stack[-1][0]][lhs], TreeNode(symbol=lhs, children=kids)))
    return SlrRun(trace=trace, tree=None, accepted=False)
