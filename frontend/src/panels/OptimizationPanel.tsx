import { useStore } from "../state/store";
import { Empty, useHl, WhyChip } from "../components/common";
import type { Applied, Instr } from "../types";

export default function OptimizationPanel() {
  const { response, select } = useStore();
  const hl = useHl();
  const o = response?.optimized, before = response?.tac;
  if (!before || !o) return <Empty>Enable "Optimize" and compile (errors stop the pipeline).</Empty>;
  const beforeIds = new Set(before.map((i) => i.id)), afterIds = new Set(o.tac.map((i) => i.id));
  const byAfter = new Map<string, Applied>(); const removed = new Map<string, Applied[]>();
  o.applied.forEach((a) => {
    if (a.after) byAfter.set(a.after, a);
    else a.before.forEach((b) => removed.set(b, [...(removed.get(b) ?? []), a]));
  });
  /** Every rewrite that contributed to a final line, following the origin chain back. */
  const chain = (id: string): Applied[] => {
    const a = byAfter.get(id);
    return a ? [...a.before.flatMap(chain), a] : [];
  };
  const counts = new Map<string, number>();
  o.applied.forEach((a) => counts.set(a.rule_id, (counts.get(a.rule_id) ?? 0) + 1));
  const line = (i: Instr, changed: boolean, chips: Applied[]) => (
    <li key={i.id} onClick={() => select([i.id])}
      className={`flex items-center gap-2 px-3 py-0.5 font-mono text-sm ${hl(i.id) ? "hl-row" : ""} ${changed ? "bg-amber-500/10" : ""} cursor-pointer`}>
      <span className="flex-1">{i.op === "label" ? i.text : "    " + i.text}</span>
      {chips.map((a) => <span key={a.id} title={a.explanation.title}><WhyChip e={a.explanation} /></span>)}
    </li>);
  return (
    <div className="p-2">
      <div className="grid grid-cols-2 gap-2">
        <div><h4 className="th">Before</h4><ol>
          {before.map((i) => line(i, !afterIds.has(i.id), removed.get(i.id) ?? []))}</ol></div>
        <div><h4 className="th">After</h4><ol>
          {o.tac.map((i) => line(i, !beforeIds.has(i.id), chain(i.id)))}</ol></div>
      </div>
      <h4 className="th mt-4">Applied rules ({o.applied.length})</h4>
      <ul className="p-2 text-sm">
        {[...counts].map(([r, n]) => <li key={r}><span className="font-mono text-xs text-accent">{r}</span> ×{n}</li>)}
        {o.applied.map((a) => (
          <li key={a.id} onClick={() => select([a.id])} className={`flex cursor-pointer items-center gap-2 font-mono text-xs ${hl(a.id) ? "hl-row" : ""}`}>
            <span className="text-slate-400">{a.rule_id}</span><span>{a.explanation.detail.before} → {a.explanation.detail.after}</span>
            <WhyChip e={a.explanation} />
          </li>))}
      </ul>
    </div>
  );
}
