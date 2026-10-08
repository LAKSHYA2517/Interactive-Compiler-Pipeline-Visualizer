"""Optimizer rule table: {rule_id: title, reason_template, concept}."""
RULES = {
    "OPT_CONST_FOLD": {
        "title": "Constant folding",
        "reason_template": "Both operands of '{before}' are known at compile time, so the result is computed now instead of at run time.",
        "concept": "Constant folding",
    },
    "OPT_CONST_PROP": {
        "title": "Constant propagation",
        "reason_template": "Inside this basic block '{var}' always holds {value}, so the use is replaced by the constant.",
        "concept": "Constant propagation within a basic block",
    },
    "OPT_ALGEBRAIC": {
        "title": "Algebraic simplification",
        "reason_template": "'{before}' applies an identity ({identity}), so no computation is needed.",
        "concept": "Algebraic identities / strength reduction",
    },
    "OPT_COPY_PROP": {
        "title": "Copy propagation",
        "reason_template": "{why}",
        "concept": "Copy propagation and copy forwarding",
    },
    "OPT_CSE": {
        "title": "Common subexpression elimination",
        "reason_template": "'{expr}' was already computed into {holder} and neither operand changed since, so that value is reused.",
        "concept": "Local common subexpression elimination",
    },
    "OPT_DEAD_CODE": {
        "title": "Dead code elimination",
        "reason_template": "Temporary '{var}' is assigned but never read, so '{before}' has no effect and is removed.",
        "concept": "Dead code elimination (liveness of temporaries)",
    },
    "OPT_PEEPHOLE": {
        "title": "Peephole cleanup",
        "reason_template": "{why}",
        "concept": "Peephole optimization of jumps and labels",
    },
}
ALL_PASSES = list(RULES)
