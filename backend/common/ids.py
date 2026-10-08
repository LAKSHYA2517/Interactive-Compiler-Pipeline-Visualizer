"""Deterministic per-compile id counters: tok_0, ast_0, diag_0, tac_0, opt_0, app_0."""


class IdGen:
    def __init__(self) -> None:
        self._n: dict[str, int] = {}

    def next(self, prefix: str) -> str:
        n = self._n.get(prefix, 0)
        self._n[prefix] = n + 1
        return f"{prefix}_{n}"


def symbol_id(name: str, scope: str) -> str:
    return f"sym_{name}_{scope}"
