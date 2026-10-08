"""Basic blocks. Leader: first instruction, any label, any instruction after goto/if_goto."""
from .tac import Instr


def split(instrs: list[Instr]) -> list[list[Instr]]:
    blocks: list[list[Instr]] = []
    prev_jump = True
    for i in instrs:
        if prev_jump or i.op == "label":
            blocks.append([])
        blocks[-1].append(i)
        prev_jump = i.op in ("goto", "if_goto")
    return blocks
