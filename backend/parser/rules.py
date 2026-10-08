"""Syntax-phase (and lexer) rule table: data, not inline strings."""
RULES = {
    "LEX_UNKNOWN_CHAR": {
        "title": "Unknown character",
        "reason_template": "The scanner found '{ch}', which starts no MiniLang token, so it was skipped.",
        "concept": "Lexical analysis: characters outside the alphabet are lexical errors.",
    },
    "SYN_UNEXPECTED_TOKEN": {
        "title": "Unexpected token",
        "reason_template": "The grammar allows only {expected} here, but the parser found '{found}'.",
        "concept": "Predictive parsing: FIRST sets decide which production applies.",
    },
    "SYN_MISSING_SEMICOLON": {
        "title": "Missing semicolon",
        "reason_template": "A statement must end with ';' but the parser found '{found}'.",
        "concept": "Statement terminators in the grammar.",
    },
}
