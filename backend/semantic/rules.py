"""Semantic rule table: {rule_id: title, reason_template, concept}."""
RULES = {
    "SEM_UNDECLARED": {
        "title": "Undeclared variable",
        "reason_template": "'{name}' is looked up from the current scope outward ({scopes}) and no declaration was found.",
        "concept": "Symbol table lookup: a name must be declared before use.",
    },
    "SEM_REDECLARED": {
        "title": "Redeclaration in same scope",
        "reason_template": "Scope '{scope}' already contains '{name}'; a scope may declare each name only once.",
        "concept": "Scope rules: unique names per scope, shadowing allowed across scopes.",
    },
    "SEM_TYPE_MISMATCH": {
        "title": "Type mismatch in assignment",
        "reason_template": "The target has type {lhs} but the value has type {rhs}. Only an exact match or int into float is allowed.",
        "concept": "Type checking: assignment compatibility.",
    },
    "SEM_BAD_OPERAND": {
        "title": "Operator does not accept operand type",
        "reason_template": "'{op}' requires {needs}, but an operand has type {type}.",
        "concept": "Type checking: operator typing rules.",
    },
    "SEM_COND_NOT_BOOL": {
        "title": "Condition must be bool",
        "reason_template": "if/while conditions must have type bool, but this expression has type {type}.",
        "concept": "Type checking: control-flow conditions.",
    },
    "SEM_UNINIT_USE": {
        "title": "Possible use before assignment",
        "reason_template": "'{name}' was declared without a value and no assignment appears before this read.",
        "concept": "Simple forward pass over declarations and assignments (not flow-sensitive).",
    },
}
