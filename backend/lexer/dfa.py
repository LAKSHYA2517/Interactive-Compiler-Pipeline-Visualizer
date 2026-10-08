"""Subset construction + simulation. Concept: NFA -> DFA (epsilon-closure and move)."""
from pydantic import BaseModel

from .nfa import NFA, RawNFA, build_nfa, nfa_json
from .regex import Atom


class DfaState(BaseModel):
    id: str
    nfa_states: list[str]


class DFA(BaseModel):
    states: list[DfaState]
    start: str
    accept: list[str]
    transitions: list[dict]


class Step(BaseModel):
    index: int
    char: str
    from_state: str
    to_state: str | None
    accepted_so_far: bool


class DfaResult(BaseModel):
    nfa: NFA
    dfa: DFA
    steps: list[Step]
    accepted: bool


def pieces(atoms: list[Atom]) -> list[Atom]:
    """Refine atoms into disjoint pieces so every char falls in exactly one DFA symbol."""
    cuts = sorted({lo for a in atoms for lo, _ in a.ranges} | {hi + 1 for a in atoms for _, hi in a.ranges})
    groups: dict[frozenset, list[tuple[int, int]]] = {}
    for lo, nxt in zip(cuts, cuts[1:]):
        sig = frozenset(a.label for a in atoms if a.has(chr(lo)))
        if sig:
            groups.setdefault(sig, []).append((lo, nxt - 1))
    out = []
    for sig, rs in groups.items():
        same = [a for a in atoms if a.label in sig and sorted(a.ranges) == rs]
        label = same[0].label if same else "[" + "".join(
            chr(lo) if lo == hi else f"{chr(lo)}-{chr(hi)}" for lo, hi in rs) + "]"
        out.append(Atom(label, tuple(rs)))
    return out


def closure(nfa: RawNFA, states: set[int]) -> frozenset[int]:
    seen, work = set(states), list(states)
    while work:
        s = work.pop()
        for a, b, x in nfa.edges:
            if a == s and x is None and b not in seen:
                seen.add(b)
                work.append(b)
    return frozenset(seen)


def build(regex: str, test_input: str | None = None) -> DfaResult:
    nfa, start, accept = build_nfa(regex)
    syms = pieces([x for _, _, x in nfa.edges if x is not None])
    s0 = closure(nfa, {start})
    names = {s0: "D0"}
    order, trans, work = [s0], [], [s0]
    while work:
        cur = work.pop(0)
        for sym in syms:
            mv = {b for a, b, x in nfa.edges if a in cur and x is not None and x.has(chr(sym.ranges[0][0]))}
            if not mv:
                continue
            nxt = closure(nfa, mv)
            if nxt not in names:
                names[nxt] = f"D{len(names)}"
                order.append(nxt)
                work.append(nxt)
            trans.append({"from": names[cur], "to": names[nxt], "symbol": sym.label})
    dfa = DFA(states=[DfaState(id=names[s], nfa_states=[f"q{i}" for i in sorted(s)]) for s in order],
              start="D0", accept=[names[s] for s in order if accept in s], transitions=trans)
    steps, cur, ok = [], "D0", True
    for k, ch in enumerate(test_input or ""):
        sym = next((p for p in syms if p.has(ch)), None)
        t = next((t for t in trans if t["from"] == cur and sym and t["symbol"] == sym.label), None)
        nxt = t["to"] if t else None
        steps.append(Step(index=k, char=ch, from_state=cur, to_state=nxt, accepted_so_far=nxt in dfa.accept))
        if nxt is None:
            ok = False
            break
        cur = nxt
    return DfaResult(nfa=nfa_json(nfa, start, accept), dfa=dfa, steps=steps,
                     accepted=ok and cur in dfa.accept and test_input is not None)
