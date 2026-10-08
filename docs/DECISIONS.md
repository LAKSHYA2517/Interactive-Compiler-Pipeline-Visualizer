# Decisions and deviations

- Repo root is the project root (no extra `compiler-visualizer/` folder).
- `semantic/scope_checker.py` is folded into `type_checker.py` + `symbol_table.py` (one AST walk, as the brief asks).
- Shadowed variables get a distinct IR name `name_<scope>` (`Symbol.tac_name`) so basic-block optimizations stay correct.
- `&&` / `||` are plain boolean binops in TAC (no short-circuit).
- TAC `binop`/`unop` carry a result type `ty` so `/` is integer division for ints and true division for floats.
- Unchanged instructions keep their TAC id after optimization; changed ones get a fresh `opt_N` id with `origin` = replaced ids.
  `Applied.instr` ships the intermediate instruction too, so the origin chain from any final line reaches tokens.
- Parentheses are transparent in the AST; the inner node's span and origin are widened to include `(` and `)`.
- The lexer error for unknown characters uses rule `LEX_UNKNOWN_CHAR`, stored in `parser/rules.py`.
- A lexer error does not stop the parser (so more errors show); any error stops semantic analysis and later phases.
- `mock.json` was generated from the real backend for the demo program rather than written by hand.
- Backpatching view (tier 2) was cut. `/parse` returns the SLR table, trace and tree for the MiniLang grammar; CFG panel and TAC interpreter (stretch) are done.
- Constant folding does not fold `if_goto` with constant conditions; dead-code removal only deletes temporaries.
- Frontend uses React 18, Tailwind v4, hash routing (`#/learn`) instead of a router library.
- Regex classes do not support negation (`[^..]`) or `.`; empty-regex/unbalanced input returns HTTP 422.
