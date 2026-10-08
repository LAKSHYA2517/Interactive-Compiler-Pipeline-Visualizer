import { create } from "zustand";
import { compile } from "../api/client";
import { buildLineage, Lineage } from "../lib/lineage";
import type { CompileResponse, Explanation, Span } from "../types";

export const PASSES = ["OPT_CONST_FOLD", "OPT_CONST_PROP", "OPT_ALGEBRAIC", "OPT_COPY_PROP", "OPT_CSE", "OPT_DEAD_CODE", "OPT_PEEPHOLE"];
export const DEMO = "int a = 10;\nint b = 20;\nint c = a + b * 2;\nprint(c);\n";

interface State {
  source: string;
  optimize: boolean;
  passes: string[];
  response: CompileResponse | null;
  lineage: Lineage;
  selection: Set<string>;
  tab: string;
  loading: boolean;
  error: string | null;
  explanation: Explanation | null;
  reveal: { span: Span; tick: number } | null;
  setSource(s: string): void;
  setOptimize(b: boolean): void;
  togglePass(p: string): void;
  setTab(t: string): void;
  run(): Promise<void>;
  /** Select one or more artifacts; the selection is the union of their lineage expansions. */
  select(ids: string[]): void;
  explain(e: Explanation | null): void;
  showInSource(span: Span | null, ids?: string[]): void;
}

const empty = buildLineage(null);

export const useStore = create<State>((set, get) => ({
  source: DEMO, optimize: true, passes: [...PASSES], response: null, lineage: empty, selection: new Set(),
  tab: "Tokens", loading: false, error: null, explanation: null, reveal: null,
  setSource: (source) => set({ source }),
  setOptimize: (optimize) => set({ optimize }),
  togglePass: (p) => set((s) => ({ passes: s.passes.includes(p) ? s.passes.filter((x) => x !== p) : [...s.passes, p] })),
  setTab: (tab) => set({ tab }),
  async run() {
    const { source, optimize, passes } = get();
    set({ loading: true, error: null });
    try {
      const response = await compile(source, optimize, passes);
      set({ response, lineage: buildLineage(response), selection: new Set(), explanation: null, loading: false });
    } catch (e) {
      set({ loading: false, error: e instanceof Error ? e.message : String(e) });
    }
  },
  select(ids) {
    const { lineage } = get();
    const out = new Set<string>();
    ids.forEach((id) => lineage.expand(id).forEach((x) => out.add(x)));
    set({ selection: out });
  },
  explain: (explanation) => set({ explanation }),
  showInSource(span, ids) {
    if (ids) get().select(ids);
    if (span) set((s) => ({ reveal: { span, tick: (s.reveal?.tick ?? 0) + 1 } }));
  },
}));
