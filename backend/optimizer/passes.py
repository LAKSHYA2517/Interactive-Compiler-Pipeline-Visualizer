"""Optimization passes over TAC. Each pass: (list[Instr], Ctx) -> list[Instr].

Concept: local (basic-block) optimizations. An unchanged instruction keeps its id;
a changed one gets a fresh opt_N id whose origin lists the instructions it replaced.
"""
from pydantic import BaseModel

from ..common.explain import Explanation, explain
from ..common.ids import IdGen
from ..common.span import merge
from ..ir.basic_blocks import split
from ..ir.tac import Instr, is_lit, is_temp
from ..vm.tac_interpreter import binop, val
from .rules import RULES


class Applied(BaseModel):
    id: str
    rule_id: str
    before: list[str]           # ids of instructions consumed
    after: str | None           # id of the resulting instruction (None = deleted)
    instr: Instr | None = None  # the resulting instruction itself (may be superseded by later passes)
    explanation: Explanation


class Ctx:
    def __init__(self, ids: IdGen):
        self.ids, self.applied = ids, []

    def change(self, rule: str, old: list[Instr], why: dict | None = None,
               **fields) -> Instr | None:
        """Record a rewrite of `old` into a new instruction built from `fields` (None = delete)."""
        before = "; ".join(o.text for o in old)
        new = None
        if fields:
            base = old[-1]
            new = Instr(id=self.ids.next("opt"), op=fields.pop("op", base.op), span=merge([o.span for o in old]),
                        origin=[o.id for o in old],
                        **{**base.model_dump(exclude={"id", "op", "span", "origin", "text"}),
                           **fields})
        after = new.text if new else "(removed)"
        aid = self.ids.next("app")
        origin = [new.id] if new else [o.id for o in old]
        ex = explain(RULES, rule, origin, merge([o.span for o in old]),
                     detail={"before": before, "after": after}, before=before, **(why or {}))
        self.applied.append(Applied(id=aid, rule_id=rule, before=[o.id for o in old],
                                    after=new.id if new else None, instr=new, explanation=ex))
        return new


def _lit(v) -> str:
    if isinstance(v, bool):
        return "true" if v else "false"
    return repr(v) if isinstance(v, float) else str(v)


def const_fold(instrs: list[Instr], ctx: Ctx) -> list[Instr]:
    out = []
    for i in instrs:
        r = i
        if i.op == "binop" and is_lit(i.a) and is_lit(i.b) and not (i.operator == "/" and float(i.b) == 0):
            v = binop(i.operator, val(i.a, {}), val(i.b, {}), i.ty)
            r = ctx.change("OPT_CONST_FOLD", [i], op="copy", dest=i.dest, a=_lit(v), b=None, operator=None)
        elif i.op == "unop" and is_lit(i.a):
            x = val(i.a, {})
            r = ctx.change("OPT_CONST_FOLD", [i], op="copy", dest=i.dest, a=_lit((not x) if i.operator == "!" else -x),
                           b=None, operator=None)
        out.append(r)
    return out


def const_prop(instrs: list[Instr], ctx: Ctx) -> list[Instr]:
    out = []
    for block in split(instrs):
        facts: dict[str, str] = {}
        for i in block:
            r = i
            if i.op not in ("label", "goto"):
                sub = {f: v for f, v in ((x, facts.get(x)) for x in (i.a, i.b)) if v}
                if sub:
                    var, value = next(iter(sub.items()))
                    r = ctx.change("OPT_CONST_PROP", [i], why={"var": var, "value": value},
                                   a=facts.get(i.a, i.a), b=facts.get(i.b, i.b) if i.b else None)
            if r.op in ("copy", "binop", "unop"):
                if r.op == "copy" and is_lit(r.a):
                    facts[r.dest] = r.a
                else:
                    facts.pop(r.dest, None)
            out.append(r)
    return out


def algebraic(instrs: list[Instr], ctx: Ctx) -> list[Instr]:
    def num(x, n):
        return is_lit(x) and x not in ("true", "false") and float(x) == n

    out = []
    for i in instrs:
        r = i
        if i.op == "binop":
            op, a, b = i.operator, i.a, i.b
            res = ident = None
            if (op == "+" and num(b, 0)) or (op == "-" and num(b, 0)) or (op == "*" and num(b, 1)) or (op == "/" and num(b, 1)):
                res, ident = a, f"x {op} {b} = x"
            elif (op == "+" and num(a, 0)) or (op == "*" and num(a, 1)):
                res, ident = b, f"{a} {op} x = x"
            elif op == "*" and (num(a, 0) or num(b, 0)):
                res, ident = ("0.0" if i.ty == "float" else "0"), "x * 0 = 0"
            if res is not None:
                r = ctx.change("OPT_ALGEBRAIC", [i], why={"identity": ident}, op="copy", dest=i.dest, a=res, b=None,
                               operator=None)
        out.append(r)
    return out


def _count_reads(instrs: list[Instr]) -> dict[str, int]:
    c: dict[str, int] = {}
    for i in instrs:
        for x in i.reads():
            c[x] = c.get(x, 0) + 1
    return c


def copy_prop(instrs: list[Instr], ctx: Ctx) -> list[Instr]:
    # forward `tN = expr; x = tN` -> `x = expr` when tN has no other use
    reads = _count_reads(instrs)
    fwd: list[Instr] = []
    k = 0
    while k < len(instrs):
        i = instrs[k]
        nxt = instrs[k + 1] if k + 1 < len(instrs) else None
        if (i.op in ("binop", "unop", "copy") and is_temp(i.dest) and nxt and nxt.op == "copy" and nxt.a == i.dest
                and reads.get(i.dest) == 1 and not is_temp(nxt.dest)):
            why = f"Temporary {i.dest} is read only by '{nxt.text}', so the computation is assigned directly to {nxt.dest}."
            fwd.append(ctx.change("OPT_COPY_PROP", [i, nxt], why={"why": why}, op=i.op, dest=nxt.dest,
                                  a=i.a, b=i.b, operator=i.operator, ty=i.ty))
            k += 2
        else:
            fwd.append(i)
            k += 1
    out = []
    for block in split(fwd):
        facts: dict[str, str] = {}
        for i in block:
            r = i
            if i.op not in ("label", "goto") and (i.a in facts or i.b in facts):
                var = i.a if i.a in facts else i.b
                why = f"'{var}' is a plain copy of '{facts[var]}' here, so the original is used directly."
                r = ctx.change("OPT_COPY_PROP", [i], why={"why": why}, a=facts.get(i.a, i.a),
                               b=facts.get(i.b, i.b) if i.b else None)
            if r.dest and r.op in ("copy", "binop", "unop"):
                facts.pop(r.dest, None)
                for f in [f for f, s in facts.items() if s == r.dest]:
                    del facts[f]
                if r.op == "copy" and not is_lit(r.a) and r.a != r.dest:
                    facts[r.dest] = r.a
            out.append(r)
    return out


def cse(instrs: list[Instr], ctx: Ctx) -> list[Instr]:
    out = []
    for block in split(instrs):
        avail: dict[tuple, str] = {}
        for i in block:
            r = i
            if i.op in ("binop", "unop"):
                key = (i.op, i.operator, i.a, i.b)
                if key in avail and avail[key] != i.dest:
                    holder = avail[key]
                    r = ctx.change("OPT_CSE", [i], why={"expr": i.text.split(" = ", 1)[1], "holder": holder},
                                   op="copy", dest=i.dest, a=holder, b=None, operator=None)
            if r.dest and r.op in ("copy", "binop", "unop"):
                for k in [k for k, h in avail.items() if h == r.dest or r.dest in (k[2], k[3])]:
                    del avail[k]
                if r.op in ("binop", "unop") and r.dest not in (r.a, r.b):
                    avail[(r.op, r.operator, r.a, r.b)] = r.dest
            out.append(r)
    return out


def dead_code(instrs: list[Instr], ctx: Ctx) -> list[Instr]:
    reads = _count_reads(instrs)
    out = []
    for i in instrs:
        if i.op in ("copy", "binop", "unop") and is_temp(i.dest) and not reads.get(i.dest):
            ctx.change("OPT_DEAD_CODE", [i], why={"var": i.dest})
        else:
            out.append(i)
    return out


def peephole(instrs: list[Instr], ctx: Ctx) -> list[Instr]:
    out: list[Instr] = []
    for k, i in enumerate(instrs):
        nxt = instrs[k + 1] if k + 1 < len(instrs) else None
        if i.op == "goto" and nxt and nxt.op == "label" and nxt.label == i.label:
            ctx.change("OPT_PEEPHOLE", [i], why={"why": f"'{i.text}' jumps to the very next instruction, so it is a no-op."})
        else:
            out.append(i)
    used = {i.label for i in out if i.op in ("goto", "if_goto")}
    final = []
    for i in out:
        if i.op == "label" and i.label not in used:
            ctx.change("OPT_PEEPHOLE", [i], why={"why": f"No jump targets label {i.label}, so the label is removed."})
        else:
            final.append(i)
    return final


PASSES = {"OPT_CONST_FOLD": const_fold, "OPT_CONST_PROP": const_prop, "OPT_ALGEBRAIC": algebraic,
          "OPT_COPY_PROP": copy_prop, "OPT_CSE": cse, "OPT_DEAD_CODE": dead_code, "OPT_PEEPHOLE": peephole}
