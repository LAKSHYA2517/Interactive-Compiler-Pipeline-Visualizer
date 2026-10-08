# API contract

Generated from the Pydantic models. Full OpenAPI: `make contract` or GET /openapi.json.

| Endpoint | Request | Response |
|---|---|---|
| GET /health | - | - |
| POST /compile | CompileReq | CompileResponse |
| POST /tokenize | SourceReq | TokenizeResponse |
| POST /build-dfa | DfaReq | DfaResult |
| POST /parse | SourceReq | ParseResponse |
| POST /semantic-analysis | SourceReq | SemanticResponse |
| POST /generate-ir | SourceReq | IrResponse |
| POST /optimize | OptimizeReq | OptimizeResponse |
| POST /grammar/analyze | GrammarReq | GrammarResponse |

## Schemas
### Applied
- `id`: {"type": "string", "title": "Id"}
- `rule_id`: {"type": "string", "title": "Rule Id"}
- `before`: {"items": {"type": "string"}, "type": "array", "title": "Before"}
- `after`: {"anyOf": [{"type": "string"}, {"type": "null"}], "title": "After"}
- `instr`: {"anyOf": [{"$ref": "#/components/schemas/Instr"}, {"type": "null"}]}
- `explanation`: {"$ref": "#/components/schemas/Explanation"}
### AstNode
- `id`: {"type": "string", "title": "Id"}
- `kind`: {"type": "string", "title": "Kind"}
- `span`: {"$ref": "#/components/schemas/Span"}
- `origin`: {"items": {"type": "string"}, "type": "array", "title": "Origin"}
- `children`: {"items": {"$ref": "#/components/schemas/AstNode"}, "type": "array", "title": "Children", "default": []}
- `operator`: {"anyOf": [{"type": "string"}, {"type": "null"}], "title": "Operator"}
- `var_type`: {"anyOf": [{"type": "string"}, {"type": "null"}], "title": "Var Type"}
- `name`: {"anyOf": [{"type": "string"}, {"type": "null"}], "title": "Name"}
- `value`: {"anyOf": [{"type": "string"}, {"type": "null"}], "title": "Value"}
- `lit_type`: {"anyOf": [{"type": "string"}, {"type": "null"}], "title": "Lit Type"}
- `type`: {"anyOf": [{"type": "string"}, {"type": "null"}], "title": "Type"}
- `symbol`: {"anyOf": [{"type": "string"}, {"type": "null"}], "title": "Symbol"}
- `error`: {"type": "boolean", "title": "Error", "default": false}
### CompileReq
- `source`: {"type": "string", "title": "Source"}
- `optimize`: {"type": "boolean", "title": "Optimize", "default": false}
- `passes`: {"anyOf": [{"items": {"type": "string"}, "type": "array"}, {"type": "null"}], "title": "Passes"}
### CompileResponse
- `ok`: {"type": "boolean", "title": "Ok"}
- `source`: {"type": "string", "title": "Source"}
- `tokens`: {"anyOf": [{"items": {"$ref": "#/components/schemas/Token"}, "type": "array"}, {"type": "null"}], "title": "Tokens"}
- `ast`: {"anyOf": [{"$ref": "#/components/schemas/AstNode"}, {"type": "null"}]}
- `symbols`: {"anyOf": [{"items": {"$ref": "#/components/schemas/Symbol"}, "type": "array"}, {"type": "null"}], "title": "Symbols"}
- `diagnostics`: {"items": {"$ref": "#/components/schemas/Diagnostic"}, "type": "array", "title": "Diagnostics", "default": []}
- `tac`: {"anyOf": [{"items": {"$ref": "#/components/schemas/Instr"}, "type": "array"}, {"type": "null"}], "title": "Tac"}
- `optimized`: {"anyOf": [{"$ref": "#/components/schemas/Optimized"}, {"type": "null"}]}
- `phases`: {"$ref": "#/components/schemas/PhaseStatus", "default": {"lexer": "skipped", "parser": "skipped", "semantic": "skipped", "ir": "skipped", "optimizer": "skipped"}}
### Conflict
- `state`: {"type": "integer", "title": "State"}
- `symbol`: {"type": "string", "title": "Symbol"}
- `kind`: {"type": "string", "title": "Kind"}
- `actions`: {"items": {"type": "string"}, "type": "array", "title": "Actions"}
- `items`: {"items": {"type": "string"}, "type": "array", "title": "Items"}
### DFA
- `states`: {"items": {"$ref": "#/components/schemas/DfaState"}, "type": "array", "title": "States"}
- `start`: {"type": "string", "title": "Start"}
- `accept`: {"items": {"type": "string"}, "type": "array", "title": "Accept"}
- `transitions`: {"items": {"additionalProperties": true, "type": "object"}, "type": "array", "title": "Transitions"}
### DfaReq
- `regex`: {"type": "string", "title": "Regex"}
- `test_input`: {"anyOf": [{"type": "string"}, {"type": "null"}], "title": "Test Input"}
### DfaResult
- `nfa`: {"$ref": "#/components/schemas/NFA"}
- `dfa`: {"$ref": "#/components/schemas/DFA"}
- `steps`: {"items": {"$ref": "#/components/schemas/Step"}, "type": "array", "title": "Steps"}
- `accepted`: {"type": "boolean", "title": "Accepted"}
### DfaState
- `id`: {"type": "string", "title": "Id"}
- `nfa_states`: {"items": {"type": "string"}, "type": "array", "title": "Nfa States"}
### Diagnostic
- `id`: {"type": "string", "title": "Id"}
- `severity`: {"type": "string", "enum": ["error", "warning"], "title": "Severity"}
- `phase`: {"type": "string", "enum": ["lexer", "parser", "semantic"], "title": "Phase"}
- `message`: {"type": "string", "title": "Message"}
- `span`: {"$ref": "#/components/schemas/Span"}
- `origin`: {"items": {"type": "string"}, "type": "array", "title": "Origin"}
- `explanation`: {"$ref": "#/components/schemas/Explanation"}
### Explanation
- `rule_id`: {"type": "string", "title": "Rule Id"}
- `title`: {"type": "string", "title": "Title"}
- `reason`: {"type": "string", "title": "Reason"}
- `detail`: {"additionalProperties": true, "type": "object", "title": "Detail", "default": {}}
- `origin`: {"items": {"type": "string"}, "type": "array", "title": "Origin"}
- `span`: {"anyOf": [{"$ref": "#/components/schemas/Span"}, {"type": "null"}]}
### GrammarReq
- `grammar_text`: {"type": "string", "title": "Grammar Text"}
- `test_input`: {"anyOf": [{"type": "string"}, {"type": "null"}], "title": "Test Input"}
### GrammarResponse
- `first`: {"additionalProperties": {"items": {"type": "string"}, "type": "array"}, "type": "object", "title": "First"}
- `follow`: {"additionalProperties": {"items": {"type": "string"}, "type": "array"}, "type": "object", "title": "Follow"}
- `table`: {"$ref": "#/components/schemas/SlrTable"}
- `conflicts`: {"items": {}, "type": "array", "title": "Conflicts"}
- `run`: {"anyOf": [{"$ref": "#/components/schemas/SlrRun"}, {"type": "null"}]}
### Instr
- `id`: {"type": "string", "title": "Id"}
- `op`: {"type": "string", "enum": ["binop", "unop", "copy", "label", "goto", "if_goto", "print"], "title": "Op"}
- `dest`: {"anyOf": [{"type": "string"}, {"type": "null"}], "title": "Dest"}
- `a`: {"anyOf": [{"type": "string"}, {"type": "null"}], "title": "A"}
- `b`: {"anyOf": [{"type": "string"}, {"type": "null"}], "title": "B"}
- `operator`: {"anyOf": [{"type": "string"}, {"type": "null"}], "title": "Operator"}
- `label`: {"anyOf": [{"type": "string"}, {"type": "null"}], "title": "Label"}
- `ty`: {"anyOf": [{"type": "string"}, {"type": "null"}], "title": "Ty"}
- `span`: {"$ref": "#/components/schemas/Span"}
- `origin`: {"items": {"type": "string"}, "type": "array", "title": "Origin"}
- `text`: {"type": "string", "title": "Text", "readOnly": true}
### IrResponse
- `tac`: {"anyOf": [{"items": {"$ref": "#/components/schemas/Instr"}, "type": "array"}, {"type": "null"}], "title": "Tac"}
- `diagnostics`: {"items": {"$ref": "#/components/schemas/Diagnostic"}, "type": "array", "title": "Diagnostics", "default": []}
### NFA
- `states`: {"items": {"type": "string"}, "type": "array", "title": "States"}
- `start`: {"type": "string", "title": "Start"}
- `accept`: {"items": {"type": "string"}, "type": "array", "title": "Accept"}
- `transitions`: {"items": {"additionalProperties": true, "type": "object"}, "type": "array", "title": "Transitions"}
### OptimizeReq
- `source`: {"type": "string", "title": "Source"}
- `passes`: {"anyOf": [{"items": {"type": "string"}, "type": "array"}, {"type": "null"}], "title": "Passes"}
### OptimizeResponse
- `before`: {"anyOf": [{"items": {"$ref": "#/components/schemas/Instr"}, "type": "array"}, {"type": "null"}], "title": "Before"}
- `after`: {"anyOf": [{"items": {"$ref": "#/components/schemas/Instr"}, "type": "array"}, {"type": "null"}], "title": "After"}
- `applied`: {"items": {"$ref": "#/components/schemas/Applied"}, "type": "array", "title": "Applied", "default": []}
- `diagnostics`: {"items": {"$ref": "#/components/schemas/Diagnostic"}, "type": "array", "title": "Diagnostics", "default": []}
### Optimized
- `tac`: {"items": {"$ref": "#/components/schemas/Instr"}, "type": "array", "title": "Tac"}
- `applied`: {"items": {"$ref": "#/components/schemas/Applied"}, "type": "array", "title": "Applied"}
### ParseResponse
- `ast`: {"anyOf": [{"$ref": "#/components/schemas/AstNode"}, {"type": "null"}]}
- `diagnostics`: {"items": {"$ref": "#/components/schemas/Diagnostic"}, "type": "array", "title": "Diagnostics"}
- `table`: {"anyOf": [{"$ref": "#/components/schemas/SlrTable"}, {"type": "null"}]}
- `slr`: {"anyOf": [{"$ref": "#/components/schemas/SlrRun"}, {"type": "null"}]}
### PhaseStatus
- `lexer`: {"type": "string", "title": "Lexer", "default": "skipped"}
- `parser`: {"type": "string", "title": "Parser", "default": "skipped"}
- `semantic`: {"type": "string", "title": "Semantic", "default": "skipped"}
- `ir`: {"type": "string", "title": "Ir", "default": "skipped"}
- `optimizer`: {"type": "string", "title": "Optimizer", "default": "skipped"}
### SemanticResponse
- `symbols`: {"anyOf": [{"items": {"$ref": "#/components/schemas/Symbol"}, "type": "array"}, {"type": "null"}], "title": "Symbols"}
- `diagnostics`: {"items": {"$ref": "#/components/schemas/Diagnostic"}, "type": "array", "title": "Diagnostics"}
- `ast`: {"anyOf": [{"$ref": "#/components/schemas/AstNode"}, {"type": "null"}]}
### SlrRun
- `trace`: {"items": {"$ref": "#/components/schemas/TraceStep"}, "type": "array", "title": "Trace"}
- `tree`: {"anyOf": [{"$ref": "#/components/schemas/TreeNode"}, {"type": "null"}]}
- `accepted`: {"type": "boolean", "title": "Accepted"}
### SlrTable
- `productions`: {"items": {"type": "string"}, "type": "array", "title": "Productions"}
- `states`: {"items": {"additionalProperties": true, "type": "object"}, "type": "array", "title": "States"}
- `action`: {"additionalProperties": {"additionalProperties": {"type": "string"}, "type": "object"}, "type": "object", "title": "Action"}
- `goto`: {"additionalProperties": {"additionalProperties": {"type": "integer"}, "type": "object"}, "type": "object", "title": "Goto"}
- `conflicts`: {"items": {"$ref": "#/components/schemas/Conflict"}, "type": "array", "title": "Conflicts"}
- `first`: {"additionalProperties": {"items": {"type": "string"}, "type": "array"}, "type": "object", "title": "First"}
- `follow`: {"additionalProperties": {"items": {"type": "string"}, "type": "array"}, "type": "object", "title": "Follow"}
### SourceReq
- `source`: {"type": "string", "title": "Source"}
### Span
- `start`: {"type": "integer", "title": "Start"}
- `end`: {"type": "integer", "title": "End"}
- `line`: {"type": "integer", "title": "Line"}
- `col`: {"type": "integer", "title": "Col"}
- `end_line`: {"type": "integer", "title": "End Line"}
- `end_col`: {"type": "integer", "title": "End Col"}
### Step
- `index`: {"type": "integer", "title": "Index"}
- `char`: {"type": "string", "title": "Char"}
- `from_state`: {"type": "string", "title": "From State"}
- `to_state`: {"anyOf": [{"type": "string"}, {"type": "null"}], "title": "To State"}
- `accepted_so_far`: {"type": "boolean", "title": "Accepted So Far"}
### Symbol
- `id`: {"type": "string", "title": "Id"}
- `name`: {"type": "string", "title": "Name"}
- `type`: {"type": "string", "title": "Type"}
- `scope`: {"type": "string", "title": "Scope"}
- `decl`: {"type": "string", "title": "Decl"}
- `uses`: {"items": {"type": "string"}, "type": "array", "title": "Uses", "default": []}
- `initialized`: {"type": "boolean", "title": "Initialized", "default": false}
- `tac_name`: {"type": "string", "title": "Tac Name"}
- `span`: {"$ref": "#/components/schemas/Span"}
- `origin`: {"items": {"type": "string"}, "type": "array", "title": "Origin"}
### Token
- `id`: {"type": "string", "title": "Id"}
- `type`: {"type": "string", "title": "Type"}
- `lexeme`: {"type": "string", "title": "Lexeme"}
- `span`: {"$ref": "#/components/schemas/Span"}
- `origin`: {"items": {"type": "string"}, "type": "array", "title": "Origin", "default": []}
### TokenizeResponse
- `tokens`: {"items": {"$ref": "#/components/schemas/Token"}, "type": "array", "title": "Tokens"}
- `diagnostics`: {"items": {"$ref": "#/components/schemas/Diagnostic"}, "type": "array", "title": "Diagnostics"}
### TraceStep
- `step`: {"type": "integer", "title": "Step"}
- `stack`: {"type": "string", "title": "Stack"}
- `input`: {"type": "string", "title": "Input"}
- `action`: {"type": "string", "title": "Action"}
### TreeNode
- `symbol`: {"type": "string", "title": "Symbol"}
- `lexeme`: {"anyOf": [{"type": "string"}, {"type": "null"}], "title": "Lexeme"}
- `token_id`: {"anyOf": [{"type": "string"}, {"type": "null"}], "title": "Token Id"}
- `children`: {"items": {"$ref": "#/components/schemas/TreeNode"}, "type": "array", "title": "Children", "default": []}