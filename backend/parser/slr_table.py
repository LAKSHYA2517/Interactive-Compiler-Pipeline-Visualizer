"""LR(0) item sets and the SLR(1) ACTION/GOTO table with a conflict report."""
from pydantic import BaseModel

from .first_follow import END, first_follow
from .grammar import Grammar

Item = tuple[int, int]  # (production index, dot position)


class Conflict(BaseModel):
    state: int
    symbol: str
    kind: str             # shift/reduce | reduce/reduce
    actions: list[str]
    items: list[str]


class SlrTable(BaseModel):
    productions: list[str]
    states: list[dict]                # {id, items: [str]}
    action: dict[int, dict[str, str]]  # s<k> | r<k> | acc
    goto: dict[int, dict[str, int]]
    conflicts: list[Conflict]
    first: dict[str, list[str]]
    follow: dict[str, list[str]]


def item_str(g: Grammar, it: Item) -> str:
    lhs, rhs = g.productions[it[0]]
    r = list(rhs)
    r.insert(it[1], "•")
    return f"{lhs} -> {' '.join(r)}"


def closure(g: Grammar, items: set[Item]) -> frozenset[Item]:
    out, work = set(items), list(items)
    while work:
        p, d = work.pop()
        rhs = g.productions[p][1]
        if d < len(rhs) and rhs[d] in g.nonterminals:
            for k, (lhs, _) in enumerate(g.productions):
                if lhs == rhs[d] and (k, 0) not in out:
                    out.add((k, 0))
                    work.append((k, 0))
    return frozenset(out)


def goto(g: Grammar, items: frozenset[Item], sym: str) -> frozenset[Item]:
    moved = {(p, d + 1) for p, d in items if d < len(g.productions[p][1]) and g.productions[p][1][d] == sym}
    return closure(g, moved) if moved else frozenset()


def build_table(g: Grammar) -> SlrTable:
    first, follow = first_follow(g)
    start = closure(g, {(0, 0)})
    states, index, edges = [start], {start: 0}, {}
    symbols = g.nonterminals + g.terminals
    k = 0
    while k < len(states):
        for s in symbols:
            nxt = goto(g, states[k], s)
            if nxt:
                if nxt not in index:
                    index[nxt] = len(states)
                    states.append(nxt)
                edges[(k, s)] = index[nxt]
        k += 1
    action: dict[int, dict[str, list[str]]] = {i: {} for i in range(len(states))}
    gt: dict[int, dict[str, int]] = {i: {} for i in range(len(states))}
    for (i, s), j in edges.items():
        if s in g.nonterminals:
            gt[i][s] = j
        else:
            action[i].setdefault(s, []).append(f"s{j}")
    for i, st in enumerate(states):
        for p, d in sorted(st):
            lhs, rhs = g.productions[p]
            if d == len(rhs):
                if p == 0:
                    action[i].setdefault(END, []).append("acc")
                else:
                    for t in sorted(follow[lhs]):
                        action[i].setdefault(t, []).append(f"r{p}")
    conflicts, flat = [], {}
    for i, row in action.items():
        flat[i] = {}
        for t, acts in row.items():
            acts = list(dict.fromkeys(acts))
            flat[i][t] = acts[0]
            if len(acts) > 1:
                kind = "reduce/reduce" if all(a.startswith("r") for a in acts) else "shift/reduce"
                conflicts.append(Conflict(state=i, symbol=t, kind=kind, actions=acts,
                                          items=[item_str(g, it) for it in sorted(states[i])]))
    return SlrTable(productions=[f"{l} -> {' '.join(r) or 'ε'}" for l, r in g.productions],
                    states=[{"id": i, "items": [item_str(g, it) for it in sorted(s)]} for i, s in enumerate(states)],
                    action=flat, goto={i: v for i, v in gt.items() if v}, conflicts=conflicts,
                    first={k: sorted(v) for k, v in first.items() if k in g.nonterminals},
                    follow={k: sorted(v) for k, v in follow.items()})
