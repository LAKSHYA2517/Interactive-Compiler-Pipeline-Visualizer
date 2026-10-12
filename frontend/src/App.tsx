import { useEffect, useState } from "react";
import DfaTool from "./components/DfaTool";
import Editor from "./components/Editor";
import GrammarTool from "./components/GrammarTool";
import { ExplanationCard } from "./components/common";
import AsmPanel from "./panels/AsmPanel";
import AstPanel from "./panels/AstPanel";
import CfgPanel from "./panels/CfgPanel";
import DfaPanel from "./panels/DfaPanel";
import DiagnosticsPanel from "./panels/DiagnosticsPanel";
import OptimizationPanel from "./panels/OptimizationPanel";
import ParsePanel from "./panels/ParsePanel";
import SourcePanel from "./panels/SourcePanel";
import SymbolsPanel from "./panels/SymbolsPanel";
import TacPanel from "./panels/TacPanel";
import TokensPanel from "./panels/TokensPanel";
import { PASSES, useStore } from "./state/store";

const TABS: Record<string, () => JSX.Element> = {
  Source: SourcePanel, Tokens: TokensPanel, "DFA/Automata": DfaPanel, AST: AstPanel, "Parsing trace": ParsePanel,
  "Symbol table": SymbolsPanel, Diagnostics: () => <DiagnosticsPanel />, TAC: TacPanel, Optimization: OptimizationPanel, Assembly: AsmPanel, CFG: CfgPanel,
};
const STEPS: [string, keyof NonNullable<ReturnType<typeof useStore.getState>["response"]>["phases"]][] = [
  ["Lexing", "lexer"], ["Parsing", "parser"], ["Semantics", "semantic"], ["IR", "ir"], ["Optimization", "optimizer"], ["CodeGen", "codegen"]];
const COLOR = { ok: "bg-green-500", failed: "bg-red-500", skipped: "bg-slate-300 dark:bg-slate-700" };

function Stepper() {
  const phases = useStore((s) => s.response?.phases);
  return (
    <div className="flex items-center gap-1 text-xs">
      {STEPS.map(([name, key], i) => (
        <div key={key} className="flex items-center gap-1">
          {i > 0 && <span className="text-slate-400">→</span>}
          <span className={`h-2.5 w-2.5 rounded-full ${COLOR[phases?.[key] ?? "skipped"]}`} />{name}
        </div>))}
    </div>
  );
}

function Workbench({ dark }: { dark: boolean }) {
  const { tab, setTab, run, loading, error, optimize, setOptimize, passes, togglePass } = useStore();
  const Panel = TABS[tab];
  return (
    <div className="grid min-h-0 flex-1 grid-cols-[minmax(320px,2fr)_minmax(0,3fr)]">
      <div className="flex min-h-0 flex-col border-r border-slate-200 dark:border-slate-800">
        <div className="flex flex-wrap items-center gap-3 border-b border-slate-200 p-2 dark:border-slate-800">
          <button className="btn" onClick={run} disabled={loading}>{loading ? "Compiling…" : "Compile"}</button>
          <label className="flex items-center gap-1 text-sm"><input type="checkbox" checked={optimize} onChange={(e) => setOptimize(e.target.checked)} />Optimize</label>
          {optimize && (
            <details className="text-xs"><summary className="cursor-pointer">passes ({passes.length}/{PASSES.length})</summary>
              <div className="absolute z-40 rounded border border-slate-300 bg-white p-2 shadow dark:border-slate-700 dark:bg-slate-900">
                {PASSES.map((p) => <label key={p} className="flex items-center gap-1 font-mono"><input type="checkbox" checked={passes.includes(p)} onChange={() => togglePass(p)} />{p}</label>)}
              </div></details>)}
          {error && <span className="text-xs text-red-500">{error}</span>}
        </div>
        <div className="min-h-0 flex-1"><Editor dark={dark} /></div>
      </div>
      <div className="flex min-h-0 min-w-0 flex-col">
        <div className="flex flex-wrap border-b border-slate-200 dark:border-slate-800">
          {Object.keys(TABS).map((t) => (
            <button key={t} onClick={() => setTab(t)} className={`px-3 py-2 text-sm ${t === tab ? "border-b-2 border-accent font-medium text-accent" : "text-slate-500"}`}>{t}</button>))}
        </div>
        <div className="min-h-0 min-w-0 flex-1 overflow-auto"><Panel /></div>
      </div>
    </div>
  );
}

function Learn() {
  const [t, setT] = useState("regex");
  return (
    <div className="min-h-0 flex-1 overflow-auto">
      <div className="flex gap-2 border-b border-slate-200 p-2 dark:border-slate-800">
        <button className={t === "regex" ? "btn" : "btn-ghost"} onClick={() => setT("regex")}>Regex → NFA → DFA</button>
        <button className={t === "grammar" ? "btn" : "btn-ghost"} onClick={() => setT("grammar")}>Grammar → FIRST/FOLLOW → SLR</button>
      </div>
      {t === "regex" ? <DfaTool /> : <GrammarTool />}
    </div>
  );
}

export default function App() {
  const [dark, setDark] = useState(() => { try { return localStorage.getItem("theme") === "dark"; } catch { return false; } });
  const [hash, setHash] = useState(location.hash);
  useEffect(() => {
    document.documentElement.classList.toggle("dark", dark);
    try { localStorage.setItem("theme", dark ? "dark" : "light"); } catch { /* ignore */ }
  }, [dark]);
  useEffect(() => { const f = () => setHash(location.hash); addEventListener("hashchange", f); return () => removeEventListener("hashchange", f); }, []);
  const learn = hash === "#/learn";
  return (
    <div className="flex h-screen flex-col">
      <header className="flex items-center gap-4 border-b border-slate-200 px-3 py-2 dark:border-slate-800">
        <h1 className="font-semibold text-accent">MiniLang Compiler Visualizer</h1>
        <Stepper />
        <div className="ml-auto flex gap-2">
          <a className="btn-ghost" href={learn ? "#/" : "#/learn"}>{learn ? "Compiler" : "Learn"}</a>
          <button className="btn-ghost" onClick={() => setDark(!dark)}>{dark ? "☀" : "☾"}</button>
        </div>
      </header>
      {learn ? <Learn /> : <Workbench dark={dark} />}
      {!learn && <footer className="max-h-24 overflow-auto border-t border-slate-200 dark:border-slate-800"><DiagnosticsPanel compact /></footer>}
      <ExplanationCard />
    </div>
  );
}
