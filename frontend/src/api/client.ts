import type { CompileResponse, DfaResult, GrammarResponse, ParseResponse } from "../types";
import mock from "./mock.json";

/** One flag switches between the hand-made mock and the real backend. */
export const USE_MOCK = import.meta.env.VITE_USE_MOCK === "1";
const BASE = import.meta.env.VITE_API_URL ?? "http://localhost:8000";

async function post<T>(path: string, body: unknown): Promise<T> {
  const r = await fetch(BASE + path, { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(body) });
  if (!r.ok) {
    const e = await r.json().catch(() => ({}));
    throw new Error(e.detail ?? `${path} failed (${r.status})`);
  }
  return r.json();
}

export const compile = (source: string, optimize: boolean, passes: string[]) =>
  USE_MOCK ? Promise.resolve(mock as unknown as CompileResponse) : post<CompileResponse>("/compile", { source, optimize, passes });
export const buildDfa = (regex: string, test_input: string) => post<DfaResult>("/build-dfa", { regex, test_input });
export const parseSlr = (source: string) => post<ParseResponse>("/parse", { source });
export const analyzeGrammar = (grammar_text: string, test_input: string) =>
  post<GrammarResponse>("/grammar/analyze", { grammar_text, test_input });
