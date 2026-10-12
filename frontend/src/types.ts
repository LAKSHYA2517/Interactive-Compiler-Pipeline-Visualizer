export interface Span { start: number; end: number; line: number; col: number; end_line: number; end_col: number }
export interface Explanation {
  rule_id: string; title: string; reason: string; detail: Record<string, any>; origin: string[]; span: Span | null;
}
export interface Diagnostic {
  id: string; severity: "error" | "warning"; phase: "lexer" | "parser" | "semantic"; message: string;
  span: Span; origin: string[]; explanation: Explanation;
}
export interface Token { id: string; type: string; lexeme: string; span: Span; origin: string[] }
export interface AstNode {
  id: string; kind: string; span: Span; origin: string[]; children: AstNode[];
  operator?: string | null; var_type?: string | null; name?: string | null; value?: string | null;
  lit_type?: string | null; type?: string | null; symbol?: string | null; error: boolean;
}
export interface Symbol {
  id: string; name: string; type: string; scope: string; decl: string; uses: string[]; initialized: boolean;
  tac_name: string; span: Span; origin: string[]; kind: "variable" | "temp";
}
export interface Instr {
  id: string; op: string; dest?: string | null; a?: string | null; b?: string | null; operator?: string | null;
  label?: string | null; ty?: string | null; span: Span; origin: string[]; text: string;
}
export interface Applied {
  id: string; rule_id: string; before: string[]; after: string | null; instr: Instr | null; explanation: Explanation;
}
export interface AsmLine { id: string; kind: "directive" | "label" | "instr"; text: string; comment: string; span: Span; origin: string[] }
export interface Optimized { tac: Instr[]; applied: Applied[] }
export type PhaseState = "ok" | "failed" | "skipped";
export interface Phases { lexer: PhaseState; parser: PhaseState; semantic: PhaseState; ir: PhaseState; optimizer: PhaseState; codegen: PhaseState }
export interface CompileResponse {
  ok: boolean; source: string; tokens: Token[] | null; ast: AstNode | null; symbols: Symbol[] | null;
  diagnostics: Diagnostic[]; tac: Instr[] | null; optimized: Optimized | null; asm: AsmLine[] | null; asm_from: string | null;
  phases: Phases;
}
export interface DfaResult {
  nfa: { states: string[]; start: string; accept: string[]; transitions: { from: string; to: string; symbol: string }[] };
  dfa: {
    states: { id: string; nfa_states: string[] }[]; start: string; accept: string[];
    transitions: { from: string; to: string; symbol: string }[];
  };
  steps: { index: number; char: string; from_state: string; to_state: string | null; accepted_so_far: boolean }[];
  accepted: boolean;
}
export interface TreeNode { symbol: string; lexeme?: string | null; token_id?: string | null; children: TreeNode[] }
export interface SlrTable {
  productions: string[]; states: { id: number; items: string[] }[];
  action: Record<string, Record<string, string>>; goto: Record<string, Record<string, number>>;
  conflicts: { state: number; symbol: string; kind: string; actions: string[]; items: string[] }[];
  first: Record<string, string[]>; follow: Record<string, string[]>;
}
export interface SlrRun { trace: { step: number; stack: string; input: string; action: string }[]; tree: TreeNode | null; accepted: boolean }
export interface ParseResponse { ast: AstNode | null; diagnostics: Diagnostic[]; table: SlrTable | null; slr: SlrRun | null }
export interface GrammarResponse {
  first: Record<string, string[]>; follow: Record<string, string[]>; table: SlrTable; conflicts: SlrTable["conflicts"];
  run: SlrRun | null;
}
