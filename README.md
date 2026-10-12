# Interactive Compiler Pipeline Visualizer (MiniLang)

A hand-written compiler for a small language, with every phase visualised in the browser. All compiler logic is
Python (no parser generators); React only draws. Click anything and its **lineage** (tokens, AST, symbols, TAC,
optimized TAC, source characters) lights up everywhere; every diagnostic and optimizer change has a **Why?** card.

## Run

```bash
python3.11 -m venv .venv && .venv/bin/pip install -r backend/requirements.txt   # once
cd frontend && npm install && cd ..                                              # once
make backend     # http://localhost:8000  (OpenAPI docs at /docs)
make frontend    # http://localhost:5173
make test        # pytest + typecheck/build of the frontend
```

Monaco loads from a CDN, so the first page load needs internet. `VITE_USE_MOCK=1 npm run dev` runs the UI against
`frontend/src/api/mock.json` without the backend.

## Layout

`backend/` common (spans, ids, diagnostics, explanations), lexer (+ regex/NFA/DFA), parser (recursive descent + SLR(1)),
semantic, ir (TAC), optimizer, codegen (assembly), vm (TAC interpreter used by tests), api. `frontend/src/lib/lineage.ts` is the provenance graph.
Docs: `docs/MINILANG.md`, `docs/DECISIONS.md`, `docs/API_CONTRACT.md` (`make contract` dumps the full OpenAPI).

Demo: paste `int a = 10; int b = 20; int c = a + b * 2; print(c);`, Compile, click `*` in the AST; click TAC `c = t2`;
change `b` to `d` to see the undeclared-variable diagnostic; the **Learn** link has the regex→DFA and grammar→SLR tools.
