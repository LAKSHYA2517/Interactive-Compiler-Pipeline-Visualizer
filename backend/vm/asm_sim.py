"""Simulator for the assembly emitted by codegen (used by tests to check the generated code)."""
import re

IDENT = re.compile(r"^[A-Za-z_]\w*$")


def run(text: str, max_steps: int = 200000) -> list:
    mem: dict = {}
    code: list[tuple[str, list[str]]] = []
    labels: dict[str, int] = {}
    for raw in text.splitlines():
        line = raw.split(";")[0].strip()
        if not line or line in (".data", ".text"):
            continue
        m = re.match(r"^(\w+):\s*(\.word|\.float)\s+(\S+)$", line)
        if m:
            mem[m.group(1)] = float(m.group(3)) if m.group(2) == ".float" else int(m.group(3))
        elif line.endswith(":"):
            labels[line[:-1]] = len(code)
        else:
            op, _, rest = line.partition(" ")
            code.append((op, [a.strip() for a in rest.split(",")] if rest else []))
    reg: dict[str, float] = {}
    out: list = []

    def val(a: str):
        if a.startswith("R"):
            return reg[a]
        return float(a) if "." in a else int(a)

    pc = steps = 0
    while pc < len(code):
        steps += 1
        if steps > max_steps:
            raise RuntimeError("step limit")
        op, a = code[pc]
        pc += 1
        if op == "HALT":
            break
        if op == "MOV":
            reg[a[0]] = val(a[1])
        elif op == "LD":
            reg[a[0]] = mem[a[1]]
        elif op == "ST":
            mem[a[0]] = reg[a[1]]
        elif op == "ITOF":
            reg[a[0]] = float(reg[a[1]])
        elif op in ("NEG", "FNEG"):
            reg[a[0]] = -reg[a[1]]
        elif op == "NOT":
            reg[a[0]] = int(not reg[a[1]])
        elif op == "PRINT":
            out.append(reg[a[0]])
        elif op == "JMP":
            pc = labels[a[0]]
        elif op == "BNZ":
            if reg[a[0]]:
                pc = labels[a[1]]
        elif op in ("BEQ", "BNE", "BLT", "BLE", "BGT", "BGE"):
            x, y = reg[a[0]], reg[a[1]]
            if {"BEQ": x == y, "BNE": x != y, "BLT": x < y, "BLE": x <= y, "BGT": x > y, "BGE": x >= y}[op]:
                pc = labels[a[2]]
        else:
            f = op.startswith("F") and op not in ("FNEG",)
            base = op[1:] if f else op
            x, y = reg[a[1]], reg[a[2]]
            if base == "DIV":
                r = x / y if f else (abs(x) // abs(y)) * (1 if (x >= 0) == (y >= 0) else -1)
            else:
                r = {"ADD": x + y, "SUB": x - y, "MUL": x * y, "SLT": int(x < y), "SLE": int(x <= y),
                     "SGT": int(x > y), "SGE": int(x >= y), "SEQ": int(x == y), "SNE": int(x != y),
                     "AND": int(bool(x and y)), "OR": int(bool(x or y))}[base]
            reg[a[0]] = r
    return out
