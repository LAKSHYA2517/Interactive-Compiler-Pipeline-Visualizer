import { useStore } from "../state/store";
import type { Diagnostic, Explanation } from "../types";

export const useHl = () => {
  const sel = useStore((s) => s.selection);
  return (...ids: (string | undefined | null)[]) => ids.some((i) => i && sel.has(i));
};

export function WhyChip({ e }: { e: Explanation }) {
  const explain = useStore((s) => s.explain);
  return <button className="chip" onClick={(ev) => { ev.stopPropagation(); explain(e); }}>Why?</button>;
}

export function SevIcon({ d }: { d: Diagnostic }) {
  return <span className={d.severity === "error" ? "text-red-500" : "text-amber-500"}>{d.severity === "error" ? "✖" : "▲"}</span>;
}

export function Empty({ children }: { children: React.ReactNode }) {
  return <div className="p-6 text-sm text-slate-500">{children}</div>;
}

/** Floating card for one Explanation (used by diagnostics and optimizer lines). */
export function ExplanationCard() {
  const { explanation: e, explain, showInSource } = useStore();
  if (!e) return null;
  const { before, after, concept, ...rest } = e.detail;
  return (
    <div className="fixed bottom-16 right-4 z-50 w-96 rounded-lg border border-accent/40 bg-white p-4 shadow-xl dark:bg-slate-900">
      <div className="flex items-start justify-between">
        <div>
          <div className="text-xs font-mono text-accent">{e.rule_id}</div>
          <div className="font-semibold">{e.title}</div>
        </div>
        <button className="text-slate-400 hover:text-slate-700" onClick={() => explain(null)}>✕</button>
      </div>
      <p className="mt-2 text-sm">{e.reason}</p>
      {before !== undefined && (
        <div className="mt-2 grid grid-cols-2 gap-2 font-mono text-xs">
          <div className="rounded bg-red-500/10 p-2"><div className="text-[10px] text-slate-500">before</div>{before}</div>
          <div className="rounded bg-green-500/10 p-2"><div className="text-[10px] text-slate-500">after</div>{after}</div>
        </div>
      )}
      {Object.entries(rest).map(([k, v]) => <div key={k} className="mt-1 text-xs text-slate-500">{k}: {JSON.stringify(v)}</div>)}
      {concept && <div className="mt-2 text-xs italic text-slate-500">Concept: {concept}</div>}
      <button className="btn mt-3" onClick={() => showInSource(e.span, e.origin)}>Show in source</button>
    </div>
  );
}
