import { useState } from "react";
import { analyzeGrammar } from "../api/client";
import type { GrammarResponse } from "../types";
import SlrView from "./SlrView";

const SAMPLE = "E -> E + T | T\nT -> T * F | F\nF -> ( E ) | id";

/** Grammar -> FIRST/FOLLOW -> SLR table -> trace (Mode 2). */
export default function GrammarTool() {
  const [text, setText] = useState(SAMPLE);
  const [input, setInput] = useState("id + id * id");
  const [res, setRes] = useState<GrammarResponse | null>(null);
  const [err, setErr] = useState<string | null>(null);
  const go = async () => {
    try { setRes(await analyzeGrammar(text, input)); setErr(null); } catch (e) { setErr(String(e instanceof Error ? e.message : e)); setRes(null); }
  };
  return (
    <div className="p-2">
      <p className="text-xs text-slate-500">One rule per line: <code>A -&gt; x y | z</code>; use ε for empty. Terminals are symbols never on a left-hand side. Test input is whitespace-separated terminals.</p>
      <textarea className="input mt-2 h-32 w-full" value={text} onChange={(e) => setText(e.target.value)} />
      <div className="mt-2 flex gap-2">
        <input className="input flex-1" value={input} onChange={(e) => setInput(e.target.value)} />
        <button className="btn" onClick={go}>Analyze</button>
      </div>
      {err && <div className="mt-2 text-sm text-red-500">{err}</div>}
      {res && <SlrView table={res.table} run={res.run} />}
    </div>
  );
}
