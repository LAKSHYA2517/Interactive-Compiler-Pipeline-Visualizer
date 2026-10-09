import { useEffect, useRef, useState } from "react";
import type { SlrRun, SlrTable } from "../types";

/** Step slider over the shift/reduce trace + ACTION/GOTO table with conflict cells marked. */
export default function SlrView({ table, run }: { table: SlrTable; run: SlrRun | null }) {
  const [k, setK] = useState(0);
  useEffect(() => { setK(0); }, [run]);
  const steps = run?.trace ?? [];
  const cur = steps[Math.min(k, steps.length - 1)];
  const state = cur ? Number(cur.stack.split(" ").pop()) : -1;   // top-of-stack state is the last number
  const lookahead = cur?.input.split(" ")[0];
  const terms = [...new Set(Object.values(table.action).flatMap((r) => Object.keys(r)))].sort();
  const nts = [...new Set(Object.values(table.goto).flatMap((r) => Object.keys(r)))];
  const conflict = new Set(table.conflicts.map((c) => `${c.state}|${c.symbol}`));
  const row = useRef<HTMLTableRowElement>(null);
  useEffect(() => { row.current?.scrollIntoView({ block: "nearest" }); }, [state, k]);
  return (
    <div className="min-w-0 p-2 text-sm">
      {run && (
        <>
          <div className="flex items-center gap-2">
            <button className="btn-ghost" onClick={() => setK(Math.max(0, k - 1))}>◀</button>
            <input type="range" min={0} max={Math.max(0, steps.length - 1)} value={k} onChange={(e) => setK(+e.target.value)} className="flex-1" />
            <button className="btn-ghost" onClick={() => setK(Math.min(steps.length - 1, k + 1))}>▶</button>
            <span className="text-xs text-slate-500">step {k + 1}/{steps.length}</span>
            <span className={run.accepted ? "text-green-600" : "text-red-500"}>{run.accepted ? "accepted" : "rejected"}</span>
          </div>
          {cur && (
            <div className="mt-2 rounded border border-slate-200 p-2 font-mono text-xs dark:border-slate-800">
              <div><b>stack</b> {cur.stack}</div><div><b>input</b> {cur.input}</div><div><b>action</b> <span className="text-accent">{cur.action}</span></div>
            </div>)}
        </>)}
      {table.conflicts.length > 0 && (
        <div className="mt-2 rounded bg-red-500/10 p-2 text-xs">
          <b>{table.conflicts.length} conflict(s)</b>
          {table.conflicts.map((c, i) => <div key={i}>state {c.state}, '{c.symbol}': {c.kind} ({c.actions.join(" / ")})<div className="pl-3 text-slate-500">{c.items.join(" ; ")}</div></div>)}
        </div>)}
      <details className="mt-2"><summary className="cursor-pointer text-xs text-slate-500">FIRST/FOLLOW of nonterminals</summary>
      <table className="mb-3 text-xs"><tbody>
        {Object.keys(table.first).map((n) => <tr key={n}><td className="td font-mono">{n}</td><td className="td">FIRST {"{"}{table.first[n].join(", ")}{"}"}</td><td className="td">FOLLOW {"{"}{(table.follow[n] ?? []).join(", ")}{"}"}</td></tr>)}
      </tbody></table></details>
      <div className="mt-2 max-h-[55vh] overflow-auto rounded border border-slate-200 dark:border-slate-800">
        <table className="text-xs">
          <thead><tr><th className="th">state</th>{terms.map((t) => <th key={t} className="th">{t}</th>)}{nts.map((t) => <th key={t} className="th text-accent">{t}</th>)}</tr></thead>
          <tbody>
            {table.states.map((s) => (
              <tr key={s.id} ref={s.id === state ? row : undefined} className={s.id === state ? "hl-row" : ""} title={s.items.join("\n")}>
                <td className="td font-mono">{s.id}</td>
                {terms.map((t) => (
                  <td key={t} className={`td font-mono ${conflict.has(`${s.id}|${t}`) ? "bg-red-500/30" : ""} ${s.id === state && t === lookahead ? "font-bold text-accent" : ""}`}>{table.action[s.id]?.[t] ?? ""}</td>))}
                {nts.map((t) => <td key={t} className="td font-mono">{table.goto[s.id]?.[t] ?? ""}</td>)}
              </tr>))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
