"""TAC interpreter, used by tests to check optimizer correctness."""
from ..ir.tac import Instr, is_lit


def val(tok: str, env: dict):
    if tok == "true":
        return True
    if tok == "false":
        return False
    if is_lit(tok):
        return float(tok) if "." in tok else int(tok)
    return env.get(tok, 0)


def binop(op: str, a, b, ty):
    if op == "/":
        if ty == "float" or isinstance(a, float) or isinstance(b, float):
            return a / b
        q = abs(a) // abs(b)
        return q if (a >= 0) == (b >= 0) else -q
    return {"+": lambda: a + b, "-": lambda: a - b, "*": lambda: a * b, "<": lambda: a < b,
            "<=": lambda: a <= b, ">": lambda: a > b, ">=": lambda: a >= b, "==": lambda: a == b,
            "!=": lambda: a != b, "&&": lambda: a and b, "||": lambda: a or b}[op]()


def run(instrs: list[Instr], max_steps: int = 100000) -> list:
    labels = {i.label: n for n, i in enumerate(instrs) if i.op == "label"}
    env: dict = {}
    out: list = []
    pc = steps = 0
    while pc < len(instrs):
        steps += 1
        if steps > max_steps:
            raise RuntimeError("step limit")
        i = instrs[pc]
        pc += 1
        if i.op == "copy":
            env[i.dest] = val(i.a, env)
        elif i.op == "binop":
            env[i.dest] = binop(i.operator, val(i.a, env), val(i.b, env), i.ty)
        elif i.op == "unop":
            x = val(i.a, env)
            env[i.dest] = (not x) if i.operator == "!" else -x
        elif i.op == "print":
            out.append(val(i.a, env))
        elif i.op == "goto":
            pc = labels[i.label]
        elif i.op == "if_goto":
            c = val(i.a, env) if i.operator is None else binop(i.operator, val(i.a, env), val(i.b, env), None)
            if c:
                pc = labels[i.label]
    return out
