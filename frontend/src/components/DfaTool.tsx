import { useEffect, useState } from "react";
import { buildDfa } from "../api/client";
import type { DfaResult } from "../types";
import Automaton from "./Automaton";

/** Regex -> NFA -> DFA with step-by-step simulation. Also used by the /learn page. */
export default function DfaTool() {
  const [regex, setRegex] = useState("[a-zA-Z][a-zA-Z0-9]*");
  const [input, setInput] = useState("Lakshya123");
  const [res, setRes] = useState<DfaResult | null>(null);
  const [err, setErr] = useState<string | null>(null);
  const [k, setK] = useState(0);        // number of steps consumed
  const [playing, setPlaying] = useState(false);

  const build = async () => {
    try { setRes(await buildDfa(regex, input)); setErr(null); setK(0); setPlaying(false); }
    catch (e) { setErr(String(e instanceof Error ? e.message : e)); setRes(null); }
  };
  useEffect(() => { build(); /* eslint-disable-next-line */ }, []);
  useEffect(() => {
    if (!playing || !res) return;
    if (k >= res.steps.length) { setPlaying(false); return; }
    const t = setTimeout(() => setK((x) => x + 1), 600);
    return () => clearTimeout(t);
  }, [playing, k, res]);

  const steps = res?.steps ?? [];
  const last = k > 0 ? steps[k - 1] : null;
  const active = res ? (k === 0 ? res.dfa.start : last?.to_state ?? last?.from_state) : null;
  const done = res && k >= steps.length;
  return (
    <div className="flex h-full min-h-[500px] flex-col">
      <div className="flex flex-wrap items-center gap-2 border-b border-slate-200 p-2 dark:border-slate-800">
        <label className="text-xs text-slate-500">Regex</label>
        <input className="input w-64" value={regex} onChange={(e) => setRegex(e.target.value)} />
        <label className="text-xs text-slate-500">Test</label>
        <input className="input w-48" value={input} onChange={(e) => setInput(e.target.value)} />
        <button className="btn" onClick={build}>Build</button>
        <button className="btn-ghost" disabled={!res || k >= steps.length} onClick={() => setK(k + 1)}>Step</button>
        <button className="btn-ghost" disabled={!res} onClick={() => { if (done) setK(0); setPlaying(!playing); }}>{playing ? "Pause" : "Play"}</button>
        <button className="btn-ghost" onClick={() => { setK(0); setPlaying(false); }}>Reset</button>
        <span className="font-mono text-sm">
          {input.split("").map((c, i) => <span key={i} className={i < k ? "text-accent" : ""}>{c}</span>)}
        </span>
        {res && done && <span className={res.accepted ? "font-semibold text-green-600" : "font-semibold text-red-500"}>{res.accepted ? "ACCEPTED" : "REJECTED"}</span>}
      </div>
      {err && <div className="p-2 text-sm text-red-500">{err}</div>}
      {res && (
        <div className="grid flex-1 grid-rows-2 divide-y divide-slate-200 dark:divide-slate-800">
          <div><div className="th">NFA (Thompson, {res.nfa.states.length} states)</div>
            <div className="h-[calc(100%-24px)]"><Automaton {...res.nfa} /></div></div>
          <div><div className="th">DFA (subset construction, {res.dfa.states.length} states)</div>
            <div className="h-[calc(100%-24px)]">
              <Automaton states={res.dfa.states.map((s) => s.id)} start={res.dfa.start} accept={res.dfa.accept}
                transitions={res.dfa.transitions} active={active}
                activeEdge={last && last.to_state ? { from: last.from_state, to: last.to_state } : null} /></div></div>
        </div>
      )}
    </div>
  );
}
