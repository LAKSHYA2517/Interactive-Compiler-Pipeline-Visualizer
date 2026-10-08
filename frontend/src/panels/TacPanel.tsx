import { useStore } from "../state/store";
import { Empty, useHl } from "../components/common";
import type { Instr } from "../types";

/** Text with temporaries wrapped so hovering shows the source subexpression that defined them. */
export function TacText({ i, defs, source }: { i: Instr; defs: Map<string, Instr>; source: string }) {
  return (
    <>{i.text.split(/(\bt\d+\b)/).map((w, k) => {
      const d = /^t\d+$/.test(w) ? defs.get(w) : undefined;
      return d ? <span key={k} className="underline decoration-dotted" title={source.slice(d.span.start, d.span.end)}>{w}</span> : w;
    })}</>
  );
}

export const tempDefs = (tac: Instr[]) => {
  const m = new Map<string, Instr>();
  tac.forEach((i) => { if (i.dest && /^t\d+$/.test(i.dest) && !m.has(i.dest)) m.set(i.dest, i); });
  return m;
};

export default function TacPanel() {
  const { response, select, source } = useStore();
  const hl = useHl();
  if (!response?.tac) return <Empty>No TAC: fix the errors first.</Empty>;
  const defs = tempDefs(response.tac);
  return (
    <ol className="font-mono text-sm">
      {response.tac.map((i, n) => (
        <li key={i.id} onClick={() => select([i.id])} className={`flex cursor-pointer gap-3 px-3 py-0.5 ${hl(i.id) ? "hl-row" : "hover:bg-slate-100 dark:hover:bg-slate-900"}`}>
          <span className="w-6 text-right text-slate-400">{n + 1}</span>
          <span className={i.op === "label" ? "font-semibold text-accent" : "pl-4"}>
            <TacText i={i} defs={defs} source={source} /></span>
        </li>))}
    </ol>
  );
}
