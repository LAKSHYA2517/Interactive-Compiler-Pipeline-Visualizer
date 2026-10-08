"""Regex -> postfix. Concept: explicit concatenation + shunting-yard.

Syntax: literals, concatenation, | * + ? ( ), classes [a-z0-9_], escape \\.
"""
from typing import NamedTuple


class Atom(NamedTuple):
    label: str
    ranges: tuple[tuple[int, int], ...]   # inclusive code-point ranges

    def has(self, ch: str) -> bool:
        return any(lo <= ord(ch) <= hi for lo, hi in self.ranges)


OPS = {"|": 1, ".": 2, "*": 3, "+": 3, "?": 3}


def lit(ch: str) -> Atom:
    return Atom(ch, ((ord(ch), ord(ch)),))


def tokenize(rx: str) -> list:
    """Atoms and operator characters ('|', '*', '+', '?', '(', ')')."""
    out, i = [], 0
    while i < len(rx):
        c = rx[i]
        if c == "\\":
            if i + 1 >= len(rx):
                raise ValueError("Dangling escape at end of regex")
            out.append(lit(rx[i + 1]))
            i += 2
        elif c == "[":
            j = rx.find("]", i + 1)
            if j == -1 or j == i + 1:
                raise ValueError("Unterminated or empty character class")
            body, ranges, k = rx[i + 1:j], [], 0
            while k < len(body):
                if k + 2 < len(body) and body[k + 1] == "-":
                    if body[k] > body[k + 2]:
                        raise ValueError(f"Bad range {body[k:k + 3]}")
                    ranges.append((ord(body[k]), ord(body[k + 2])))
                    k += 3
                else:
                    ranges.append((ord(body[k]), ord(body[k])))
                    k += 1
            out.append(Atom(rx[i:j + 1], tuple(ranges)))
            i = j + 1
        else:
            out.append(c if c in "|*+?()" else lit(c))
            i += 1
    return out


def is_op(t, ch: str) -> bool:
    return isinstance(t, str) and t == ch


def add_concat(toks: list) -> list:
    out = []
    for k, t in enumerate(toks):
        out.append(t)
        if k + 1 < len(toks):
            left_ends = not isinstance(t, str) or t in ")*+?"
            right_starts = not isinstance(toks[k + 1], str) or toks[k + 1] == "("
            if left_ends and right_starts:
                out.append(".")
    return out


def to_postfix(rx: str) -> list:
    toks = add_concat(tokenize(rx))
    if not toks:
        raise ValueError("Empty regex")
    out, stack = [], []
    for t in toks:
        if not isinstance(t, str):
            out.append(t)
        elif t == "(":
            stack.append(t)
        elif t == ")":
            while stack and stack[-1] != "(":
                out.append(stack.pop())
            if not stack:
                raise ValueError("Unbalanced ')'")
            stack.pop()
        else:
            while stack and stack[-1] != "(" and OPS[stack[-1]] >= OPS[t]:
                out.append(stack.pop())
            stack.append(t)
    while stack:
        if stack[-1] == "(":
            raise ValueError("Unbalanced '('")
        out.append(stack.pop())
    return out
