import { useStore } from "../state/store";
import { Empty, SevIcon, useHl, WhyChip } from "../components/common";

export default function DiagnosticsPanel({ compact = false }: { compact?: boolean }) {
  const { response, showInSource } = useStore();
  const hl = useHl();
  const ds = response?.diagnostics ?? [];
  if (!ds.length) return compact ? <div className="px-3 py-1 text-xs text-slate-500">{response ? "No diagnostics ✓" : "Not compiled yet"}</div> : <Empty>No diagnostics.</Empty>;
  return (
    <ul className={compact ? "flex flex-wrap gap-x-6 gap-y-1 px-3 py-1" : ""}>
      {ds.map((d) => (
        <li key={d.id} onClick={() => showInSource(d.span, [d.id])}
          className={`flex cursor-pointer items-center gap-2 text-sm ${compact ? "" : "border-b border-slate-100 px-3 py-2 dark:border-slate-800"} ${hl(d.id) ? "hl-row" : ""}`}>
          <SevIcon d={d} />
          <span className="text-xs text-slate-400">{d.phase} {d.span.line}:{d.span.col}</span>
          <span>{d.message}</span>
          <WhyChip e={d.explanation} />
        </li>))}
    </ul>
  );
}
