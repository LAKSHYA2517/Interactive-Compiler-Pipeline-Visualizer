"""Thompson's construction. Concept: regex -> epsilon-NFA."""
from pydantic import BaseModel

from .regex import Atom, to_postfix

EPS = "ε"


class NFA(BaseModel):
    states: list[str]
    start: str
    accept: list[str]
    transitions: list[dict]  # {"from","to","symbol"}


class RawNFA:
    def __init__(self) -> None:
        self.n = 0
        self.edges: list[tuple[int, int, Atom | None]] = []

    def state(self) -> int:
        self.n += 1
        return self.n - 1


def build_nfa(regex: str) -> tuple[RawNFA, int, int]:
    nfa, stack = RawNFA(), []
    for t in to_postfix(regex):
        if not isinstance(t, str):
            s, e = nfa.state(), nfa.state()
            nfa.edges.append((s, e, t))
            stack.append((s, e))
        elif t == ".":
            (s2, e2), (s1, e1) = stack.pop(), stack.pop()
            nfa.edges.append((e1, s2, None))
            stack.append((s1, e2))
        elif t == "|":
            (s2, e2), (s1, e1) = stack.pop(), stack.pop()
            s, e = nfa.state(), nfa.state()
            nfa.edges += [(s, s1, None), (s, s2, None), (e1, e, None), (e2, e, None)]
            stack.append((s, e))
        else:  # * + ?
            s1, e1 = stack.pop()
            s, e = nfa.state(), nfa.state()
            nfa.edges += [(s, s1, None), (e1, e, None)]
            if t in "*?":
                nfa.edges.append((s, e, None))
            if t in "*+":
                nfa.edges.append((e1, s1, None))
            stack.append((s, e))
    if len(stack) != 1:
        raise ValueError("Malformed regex")
    return (nfa, *stack[0])


def nfa_json(nfa: RawNFA, start: int, accept: int) -> NFA:
    return NFA(states=[f"q{i}" for i in range(nfa.n)], start=f"q{start}", accept=[f"q{accept}"],
               transitions=[{"from": f"q{a}", "to": f"q{b}", "symbol": EPS if x is None else x.label}
                            for a, b, x in nfa.edges])
