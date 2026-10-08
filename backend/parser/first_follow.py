"""FIRST and FOLLOW sets (fixpoint iteration)."""
from .grammar import Grammar

END = "$"


def first_of_seq(seq: tuple[str, ...], first: dict[str, set[str]], nullable: set[str]) -> tuple[set[str], bool]:
    out: set[str] = set()
    for s in seq:
        out |= first.get(s, {s}) - {"ε"}
        if s not in nullable:
            return out, False
    return out, True


def first_follow(g: Grammar) -> tuple[dict[str, set[str]], dict[str, set[str]]]:
    first: dict[str, set[str]] = {t: {t} for t in g.terminals}
    first.update({n: set() for n in g.nonterminals})
    nullable: set[str] = set()
    changed = True
    while changed:
        changed = False
        for lhs, rhs in g.productions:
            f, null = first_of_seq(rhs, first, nullable)
            if not f <= first[lhs]:
                first[lhs] |= f
                changed = True
            if null and lhs not in nullable:
                nullable.add(lhs)
                changed = True
    for n in nullable:
        first[n].add("ε")
    follow: dict[str, set[str]] = {n: set() for n in g.nonterminals}
    follow[g.nonterminals[0]].add(END)
    changed = True
    while changed:
        changed = False
        for lhs, rhs in g.productions:
            for k, s in enumerate(rhs):
                if s not in follow:
                    continue
                f, null = first_of_seq(rhs[k + 1:], first, nullable)
                add = f | (follow[lhs] if null else set())
                if not add <= follow[s]:
                    follow[s] |= add
                    changed = True
    return first, follow
