"""Run the enabled passes in order until a fixpoint (max 10 rounds)."""
from pydantic import BaseModel

from ..common.ids import IdGen
from ..ir.tac import Instr
from .passes import PASSES, Applied, Ctx
from .rules import ALL_PASSES


class OptResult(BaseModel):
    tac: list[Instr]
    applied: list[Applied]


def optimize(tac: list[Instr], passes: list[str] | None = None, ids: IdGen | None = None) -> OptResult:
    enabled = ALL_PASSES if passes is None else passes
    ctx = Ctx(ids or IdGen())
    cur = list(tac)
    for _ in range(10):
        n = len(ctx.applied)
        for name in ALL_PASSES:
            if name in enabled:
                cur = PASSES[name](cur, ctx)
        if len(ctx.applied) == n:
            break
    return OptResult(tac=cur, applied=ctx.applied)
