# AGENT BRIEF: Interactive Compiler Pipeline Visualizer (MiniLang)

You are building a complete, working web application end to end: a hand-written compiler for a small language (MiniLang) whose every phase is visualized in the browser. Read this whole file before writing code. Follow the build order in section 9 and do not skip the verification steps.

## 1. Mission and non-negotiables

1. **All compiler logic is written by us in Python.** No parser generators (no ANTLR, PLY, lark), no regex-library tokenizing for the main lexer, no existing compiler used as a black box. Python's `re` may be used only for tests.
2. **React is only a visualization layer.** It never tokenizes, parses, type-checks or optimizes anything.
3. **Two novelty features are part of the core and must be designed in from the first commit:**
   - **Provenance ("compiler lineage"):** every token, AST node, symbol, diagnostic, TAC instruction and optimized instruction has a stable `id`, a source `span`, and an `origin` list. Clicking anything in any panel highlights everything connected to it, down to source characters.
   - **Explainable decisions ("Why?"):** every semantic diagnostic and every optimizer change carries an `Explanation` (`rule_id`, `title`, `reason`, `detail`, `origin`, `span`) produced from a rule table, not an ad-hoc string.
4. Each phase is an independent, pure, unit-tested module. A phase takes the previous phase's output and returns a result object; no global state.
5. Output must be deterministic (same input, same ids, same ordering) so golden tests work.
6. If something in this brief is ambiguous or contradictory, pick the simplest reading, write the decision in `docs/DECISIONS.md` (one line each), and continue. Do not stop to ask unless a decision is irreversible and could reasonably go either way.

## 2. Tech stack

- Backend: Python 3.11+, FastAPI, Pydantic v2, uvicorn, pytest. CORS enabled for `http://localhost:5173`.
- Frontend: React 18 + TypeScript + Vite, Tailwind CSS, Monaco Editor (`@monaco-editor/react`), React Flow (`@xyflow/react`) for AST, DFA and CFG graphs, a small state store (Zustand).
- Run: `uvicorn backend.api.main:app --reload` (port 8000) and `npm run dev` in `frontend/` (port 5173). Provide a root `README.md` with these commands and a `Makefile` with `make test`, `make backend`, `make frontend`.

## 3. Repo layout

```text
compiler-visualizer/
  backend/
    common/      span.py  diagnostics.py  explain.py  ids.py
    lexer/       tokenizer.py  regex.py  nfa.py  dfa.py
    parser/      grammar.py  ll1_parser.py  ast.py  first_follow.py  slr_table.py  slr_parser.py
    semantic/    symbol_table.py  type_checker.py  scope_checker.py  rules.py
    ir/          tac.py  tac_gen.py  basic_blocks.py
    optimizer/   passes.py  rules.py  driver.py
    vm/          tac_interpreter.py        # used by tests; UI use is stretch
    api/         main.py  routes.py  schemas.py  pipeline.py
    tests/       test_*.py  golden/
  frontend/
    src/         api/  state/  lib/lineage.ts  components/  panels/
  docs/          MINILANG.md  API_CONTRACT.md  DECISIONS.md
  README.md  Makefile
```

## 4. Shared contracts (implement `backend/common/` first)

### 4.1 Span

Offsets are 0-based and end-exclusive over the source string; `line` and `col` are 1-based.

```python
class Span(BaseModel):
    start: int; end: int
    line: int; col: int
    end_line: int; end_col: int
# merge(spans) returns the smallest span covering all of them
```

### 4.2 Ids and origin

`ids.py` provides a deterministic counter per prefix per compile: `tok_0`, `ast_0`, `sym_<name>_<scope>`, `diag_0`, `tac_0`, `opt_0`, `app_0`.

| Artifact | Span | origin |
| --- | --- | --- |
| Token | its characters | `[]` |
| AST node | merge of child spans (leaf: its token) | ids of tokens it consumed directly |
| Symbol | declaration identifier | `[decl AST node id]` |
| Diagnostic | offending node's span | `[AST node id]` |
| TAC instruction | span of the expression/statement it implements | `[AST node id]` |
| Optimized instruction | inherited from sources | ids of the TAC (or earlier optimized) instructions it replaced or merged |

Rule: no object is constructed without a span, and no TAC or optimized instruction without a non-empty `origin`.

### 4.3 Diagnostic and Explanation

```python
class Explanation(BaseModel):
    rule_id: str            # e.g. SEM_UNDECLARED, OPT_CONST_FOLD
    title: str
    reason: str
    detail: dict = {}       # e.g. {"before": "t1 = 10 * 2", "after": "t1 = 20"}
    origin: list[str]
    span: Span | None

class Diagnostic(BaseModel):
    id: str
    severity: Literal["error", "warning"]
    phase: Literal["lexer", "parser", "semantic"]
    message: str
    span: Span
    origin: list[str]
    explanation: Explanation
```

Rules live as data in `semantic/rules.py` and `optimizer/rules.py`: `{rule_id, title, reason_template, concept}`. Code looks rules up by id and fills the template; it never builds reason text inline.

## 5. MiniLang specification

Types: `int`, `float`, `bool`. Braces are mandatory on every `if`, `else` and `while` body. Comments: `//` to end of line (skipped by the lexer, not emitted).

Token classes: KEYWORD (`int float bool if else while print true false`), IDENTIFIER `[a-zA-Z_][a-zA-Z0-9_]*`, INT_LIT `[0-9]+`, FLOAT_LIT `[0-9]+\.[0-9]+`, OPERATOR (`+ - * / = == != < <= > >= && || !`), DELIMITER (`( ) { } ;`). Longest match; keywords by table lookup after scanning an identifier. Unknown characters produce a lexer diagnostic and are skipped.

Grammar (left-recursive and unambiguous; the recursive-descent parser implements the left-recursive rules with loops):

```text
program    -> stmt_list
stmt_list  -> stmt_list stmt | stmt
stmt       -> decl | assign | if_stmt | while_stmt | print_stmt | block
decl       -> type ID ';' | type ID '=' expr ';'
type       -> 'int' | 'float' | 'bool'
assign     -> ID '=' expr ';'
if_stmt    -> 'if' '(' expr ')' block | 'if' '(' expr ')' block 'else' block
while_stmt -> 'while' '(' expr ')' block
print_stmt -> 'print' '(' expr ')' ';'
block      -> '{' stmt_list '}'
expr       -> expr '||' and_e | and_e
and_e      -> and_e '&&' rel | rel
rel        -> add RELOP add | add
add        -> add '+' term | add '-' term | term
term       -> term '*' unary | term '/' unary | unary
unary      -> '-' unary | '!' unary | primary
primary    -> INT_LIT | FLOAT_LIT | 'true' | 'false' | ID | '(' expr ')'
```

Type rules: arithmetic needs int/float (int op int gives int, any float gives float); relational on numeric gives bool, `==`/`!=` also allowed on bool pairs; `&& || !` need bool; assignment and initializer need an exact type match or int into float (float into int is an error); `if`/`while` condition must be bool.

Scope rules: each `{ }` opens a scope named `global`, `block_1`, `block_2` in creation order. A name must be declared before use, cannot be redeclared in the same scope, and may shadow an outer name. Reading a declared-but-never-assigned variable is a warning.

## 6. Phase requirements

### 6.1 Lexer (`lexer/tokenizer.py`)

Hand-written character-by-character scanner. Token: `{id, type, lexeme, span, origin: []}`. Return `{tokens, diagnostics}`. Include an `EOF` token with an empty span at the end of input.

### 6.2 Regex, NFA, DFA (`lexer/regex.py`, `nfa.py`, `dfa.py`)

- Regex syntax: literals, concatenation, `|`, `*`, `+`, `?`, grouping `( )`, classes like `[a-zA-Z0-9_]`, escape `\`.
- Insert explicit concatenation, convert to postfix (shunting-yard), build the NFA with **Thompson's construction**, then the DFA with **subset construction** (epsilon-closure and move). Optionally minimize.
- Return JSON for `/build-dfa`: `nfa {states, start, accept, transitions[{from, to, symbol}]}`, `dfa {states[{id, nfa_states}], start, accept, transitions}`, and `steps[]` for a test string: `{index, char, from_state, to_state, accepted_so_far}` ending with an `accepted: bool`. Character classes may be shown as one edge label (e.g. `[a-zA-Z]`) in the DFA view.
- Required test: `[a-zA-Z][a-zA-Z0-9]*` accepts `Lakshya123` and rejects `1abc`.

### 6.3 Parser (`parser/ll1_parser.py`, `ast.py`)

- Recursive descent with one-token lookahead. AST node: `{id, kind, span, origin, children, ...extra}`. Kinds: `Program, Block, Decl, Assign, If, While, Print, Binary, Unary, Literal, Var`. Extra fields: `operator` (Binary, Unary), `var_type` (Decl), `name` (Var, Decl, Assign target), `value` (Literal).
- Precedence from the grammar levels. Associativity left for `+ - * / && ||`.
- Errors: a syntax diagnostic with the expected token set and the span of the unexpected token. Panic-mode recovery: skip to the next `;` or `}` and continue, so multiple errors can be reported. Diagnostics here also carry an `Explanation` (rule ids `SYN_UNEXPECTED_TOKEN`, `SYN_MISSING_SEMICOLON`).

### 6.4 SLR(1) parsing (tier 2: `first_follow.py`, `slr_table.py`, `slr_parser.py`)

Compute FIRST/FOLLOW, LR(0) item sets with closure/goto, the SLR(1) ACTION/GOTO table, and a conflict report (shift/reduce or reduce/reduce) naming the cell and the items involved. The parser runs the table and returns a trace of `{step, stack, input, action}` plus a concrete parse tree. It must accept the MiniLang grammar from section 5 without conflicts; if your table has conflicts, fix the grammar and record the change in `docs/DECISIONS.md`. Also expose it for user-supplied grammars (Mode 2).

### 6.5 Semantic analysis (`semantic/`)

One AST walk with a scope stack. Build the symbol table: `{id, name, type, scope, decl, uses[], initialized}`. Annotate each expression node with `type`. Emit diagnostics with these rule ids and message templates:

| rule_id | Trigger | Message |
| --- | --- | --- |
| SEM_UNDECLARED | name used with no visible declaration | Variable '{name}' is not declared. |
| SEM_REDECLARED | same name declared twice in one scope | '{name}' is already declared in this scope (line {line}). |
| SEM_TYPE_MISMATCH | assigned type not assignable to target | Cannot assign {rhs} to {lhs}; float to int loses information. |
| SEM_BAD_OPERAND | operator given a type it does not accept | Operator '{op}' does not accept {type}. |
| SEM_COND_NOT_BOOL | condition is not bool | Condition must be bool, found {type}. |
| SEM_UNINIT_USE (warning) | read before any assignment | '{name}' may be used before it is assigned. |

Continue after an error where possible (treat the erroring expression's type as unknown and suppress cascades). Use a simple forward pass for the uninitialized warning; it need not be flow-sensitive.

### 6.6 TAC generation (`ir/tac_gen.py`)

Quadruple list. Op kinds: `binop, unop, copy, label, goto, if_goto, print`. Text format:

```text
a = 10                 copy
t1 = b * 2             binop
t2 = -a                unop
if a < b goto L1       if_goto (condition is a single relational or a bool variable)
goto L2                goto
L1:                    label
print c                print
```

Rules: fresh temporaries `t1, t2...` for each non-leaf subexpression; `int c = a + b * 2;` must produce exactly `t1 = b * 2`, `t2 = a + t1`, `c = t2`. `if/else` and `while` use labels and the pattern from the project doc:

```text
if (a < b) { c = a; } else { c = b; }
->  if a < b goto L1
    goto L2
    L1: c = a        (emit as label L1: then c = a)
    goto L3
    L2: c = b
    L3:
```

`while (cond) body` -> `L1:` cond-test, `if cond goto L2`, `goto L3`, `L2:` body, `goto L1`, `L3:`. Short-circuit `&&` and `||` may be generated as plain boolean binops (no short-circuit) for simplicity; note it in DECISIONS.md. Every instruction gets `origin = [ast node id]` and that node's span. (Backpatching view is tier 2: if time permits, emit jumps with placeholder targets and record a patch event list.)

### 6.7 Optimizer (`optimizer/`)

Operates on TAC and returns `{tac: optimized list, applied: [{id, explanation}]}`. Passes (each can be toggled by name through the API, default all on) run in this order and repeat until nothing changes (max 10 rounds):

1. `OPT_CONST_FOLD`: evaluate binop/unop whose operands are literals.
2. `OPT_CONST_PROP`: within a basic block, replace a variable by its known constant; forget facts at labels and after any assignment to that variable.
3. `OPT_ALGEBRAIC`: `x+0`, `0+x`, `x-0`, `x*1`, `1*x`, `x/1` become a copy; `x*0` becomes 0.
4. `OPT_COPY_PROP`: replace uses of a copy's target by its source within a basic block; also forward `tN = expr; x = tN` to `x = expr` when `tN` has no other use.
5. `OPT_CSE` (tier 2): within a basic block, reuse an identical earlier computation if operands were not reassigned.
6. `OPT_DEAD_CODE`: delete assignments to temporaries that are never read. Never delete assignments to user variables or `print`.
7. `OPT_PEEPHOLE` (tier 2): remove `goto L` immediately followed by `L:`; remove unused labels.

Every changed or removed instruction yields an `applied` entry with an `Explanation` (before/after text in `detail`) and the new instruction's `origin` set to the instructions it came from. Basic-block boundaries: a leader is the first instruction, any label, and any instruction after a `goto` or `if_goto`.

Expected demo behavior for `int a = 10; int b = 20; int c = a + b * 2; print(c);`:
- Only copy forwarding enabled: `a = 10; b = 20; t1 = b * 2; c = a + t1; print c`.
- All passes enabled: `a = 10; b = 20; c = 50; print 50`.

## 7. API (`backend/api/`)

Pydantic models in `schemas.py` are the single source of truth; export the OpenAPI schema to `docs/API_CONTRACT.md`.

| Endpoint | Request | Response |
| --- | --- | --- |
| POST /compile | `{source, optimize: bool, passes?: [names]}` | full document below |
| POST /tokenize | `{source}` | `{tokens, diagnostics}` |
| POST /build-dfa | `{regex, test_input?}` | `{nfa, dfa, steps, accepted}` |
| POST /parse | `{source}` | `{ast, diagnostics}` (tier 2 adds `trace`, `table`, `tree`) |
| POST /semantic-analysis | `{source}` | `{symbols, diagnostics, ast}` |
| POST /generate-ir | `{source}` | `{tac}` |
| POST /optimize | `{source, passes?}` | `{before, after, applied}` |
| POST /grammar/analyze (tier 2) | `{grammar_text}` | `{first, follow, table, conflicts}` |

`/compile` response (a phase after the first one with errors is `null`; diagnostics from earlier phases are still returned):

```json
{
  "ok": true,
  "source": "...",
  "tokens": [],
  "ast": {},
  "symbols": [],
  "diagnostics": [],
  "tac": [],
  "optimized": { "tac": [], "applied": [] }
}
```

`pipeline.py` composes the phase functions; routes are thin. Warnings do not stop the pipeline; errors do.

## 8. Frontend requirements

Layout: left Monaco editor with Compile button and an Optimize toggle plus per-pass checkboxes; right tab area; bottom diagnostics strip. One Zustand store holds the `/compile` response and `selection: Set<string>` of artifact ids.

Tabs: Source, Tokens, DFA/Automata, AST, Parsing trace (tier 2), Symbol table, Diagnostics, TAC, Optimization, CFG (stretch).

`lib/lineage.ts`: build once per response (a) `byId` map over tokens, AST nodes (recursive), symbols, diagnostics, TAC, optimized instructions, applied entries; (b) `children` reverse index from `origin`. `expand(id)` returns the clicked item plus everything reachable by following `origin` up to the tokens and the reverse index down to dependents. Every panel highlights its items in the set; Monaco draws the union of the spans as decorations. Clicking a range in the editor selects the smallest AST node containing it.

Panel specifics:
- Tokens: table (type, lexeme, line:col).
- DFA: regex input and test-string input; draw NFA and DFA with React Flow (circles for states, double circle for accept, labelled edges); Step / Play / Reset buttons; the active state and edge highlighted per `steps`.
- AST: top-down tree with React Flow (dagre or manual layout); nodes labelled by `kind` and operator/name; error nodes red.
- Symbol table: name, type, scope, declared at, uses; clicking selects the declaration and all uses.
- Diagnostics: severity icon, message, and a **Why?** chip opening an `ExplanationCard` (title, reason, before/after, "Show in source" button). The same `ExplanationCard` is used on optimized lines.
- TAC: numbered lines; hovering a temp shows the subexpression text from the source via origin and span.
- Optimization: before and after columns side by side; changed lines marked; Why chips; list of applied rules with counts.
- Parsing trace (tier 2): step slider over `trace`; ACTION/GOTO table with conflict cells marked.
- Build the UI first against a hand-written mock `/compile` response (`frontend/src/api/mock.json`) so panels do not wait on the backend; switch to the real API through one flag.

Visual style: clean, light and dark mode, monospace for code/TAC, one accent color; keep the phase order visible as a stepper at the top (Lexing, Parsing, Semantics, IR, Optimization) showing which phases passed or failed.

Mode 2 (learning): a route `/learn` with two tools: Regex to NFA to DFA with simulation, and Grammar to FIRST/FOLLOW to table to trace (tier 2).

## 9. Build order (do each step fully, run its checks, then move on)

1. **Scaffold.** Repo layout, `README`, `Makefile`, FastAPI hello route, Vite app, CORS verified from the browser.
2. **Common.** `Span` (with merge), ids, `Diagnostic`, `Explanation`, and unit tests. Write `docs/MINILANG.md` from section 5.
3. **Contracts + mock UI.** Pydantic schemas for every response; write the mock `/compile` JSON for the demo program by hand; build the frontend shell, store, `lineage.ts` and the Source, Tokens, TAC panels against the mock. Check: clicking a TAC line highlights tokens and source in the mock.
4. **Lexer** with tests, wired to `/tokenize`; connect the Tokens panel to the real API.
5. **Parser** and AST with spans and panel; syntax-error recovery tests.
6. **Semantic analysis**, symbol table, rule table, diagnostics panel with Why chips. Check: the three error programs in section 10.
7. **TAC generation**, TAC panel, full lineage highlighting across Source, Tokens, AST, Symbols, TAC. Check: any TAC line selects its AST subtree, tokens and source range.
8. **Regex/NFA/DFA** module, `/build-dfa`, DFA panel with simulation.
9. **Optimizer** with explanations, `/optimize`, Optimization panel, pass toggles.
10. **`/compile` pipeline**, stepper, and end-to-end demo run; fix integration issues.
11. **Tier 2** in this order: peephole and CSE, SLR(1) tables and trace with panel, backpatching view.
12. **Stretch** (only if everything above passes): basic blocks and CFG panel, TAC interpreter used to assert optimized output equals original on golden programs, per-phase step scrubber.
13. **Hardening.** Run all tests, add missing invariants, manual demo, update README with screenshots-free usage notes.

After each step run `make test` and the app; if something fails, fix it before continuing.

## 10. Tests and acceptance

Golden programs (store sources and expected JSON under `backend/tests/golden/`):

| Source | Expected |
| --- | --- |
| `int a = 10; int b = 20; int c = a + b * 2; print(c);` | TAC `a = 10; b = 20; t1 = b * 2; t2 = a + t1; c = t2; print c`; optimized as in 6.7 |
| `int a; b = 10;` | SEM_UNDECLARED on `b`, message exactly "Variable 'b' is not declared." |
| `int a; a = 10.5;` | SEM_TYPE_MISMATCH |
| `int a = 1; int a = 2;` | SEM_REDECLARED |
| `int x = 5; if (x) { x = 1; }` | SEM_COND_NOT_BOOL |
| `int t = 10 * 2; int u = t + 0;` | OPT_CONST_FOLD and OPT_ALGEBRAIC entries with non-empty origin |
| `int a = 1; int b = 2; int c; if (a < b) { c = a; } else { c = b; }` | TAC matches the if/else pattern in 6.6 |
| `int i = 0; while (i < 3) { i = i + 1; }` | TAC uses labels L1..L3 per 6.6 |
| `int a = ;` | syntax diagnostic with expected tokens; parser recovers |

Automated invariants (pytest, run over every golden program):
1. Every token, AST node, symbol, diagnostic, TAC and optimized instruction has a non-empty span inside the source.
2. Following `origin` from any TAC or optimized instruction reaches at least one token.
3. Every optimizer change has an explanation whose `rule_id` exists in `optimizer/rules.py`; every diagnostic's `rule_id` exists in the semantic or parser rule table.
4. All `/compile` responses validate against the Pydantic models.
5. Same input twice gives byte-identical JSON.

Frontend checks: `npm run build` passes with no TypeScript errors; manually verify the demo script below.

## 11. Definition of done (demo script)

1. Open the app; paste the demo program; click Compile. All tabs populate.
2. Click the `*` operator in the AST: the editor highlights `b * 2`, the token rows for `b`, `*`, `2` highlight, and TAC line `t1 = b * 2` highlights.
3. Click TAC line `c = t2`: the full statement in the source, its AST subtree, and the symbol `c` highlight.
4. Change `a + b * 2` to `a + d * 2`: Diagnostics shows "Variable 'd' is not declared." with a Why chip that explains the rule and selects the span.
5. Restore the program and compile with optimization: each changed line shows a Why chip such as constant folding with before/after text; toggling a pass off changes the result.
6. DFA tab: enter `[a-zA-Z][a-zA-Z0-9]*` and test string `Lakshya123`; the animation ends in an accepting state.
7. `make test` passes from a clean checkout.

## 12. Working rules

- Small commits per step with clear messages; never leave the main branch failing tests.
- Keep functions small and typed; docstring each phase module with the syllabus concept it demonstrates (this helps the viva).
- Do not add features beyond this brief before the core and Core+ tiers pass their checks.
- When finished with each build step, record in `docs/DECISIONS.md` any place where you deviated from this brief and why.
- Final message to the team: list what is done, what was cut, how to run it, and any known bugs.
