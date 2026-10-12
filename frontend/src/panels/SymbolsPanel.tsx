import { useStore } from "../state/store";
import { Empty, useHl } from "../components/common";

export default function SymbolsPanel() {
  const { response, select } = useStore();
  const hl = useHl();
  if (!response?.symbols) return <Empty>The symbol table appears once parsing succeeds.</Empty>;
  return (
    <table className="w-full text-sm">
      <thead><tr><th className="th">Name</th><th className="th">Kind</th><th className="th">Type</th><th className="th">Scope</th><th className="th">Declared at</th><th className="th">Uses</th><th className="th">Init</th></tr></thead>
      <tbody>
        {response.symbols.map((s) => (
          <tr key={s.id} onClick={() => select([s.id, s.decl, ...s.uses])} className={`cursor-pointer ${hl(s.id) ? "hl-row" : ""}`}>
            <td className={`td font-mono ${s.kind === "temp" ? "text-slate-500" : ""}`}>{s.name}{s.tac_name !== s.name && <span className="text-xs text-slate-400"> → {s.tac_name}</span>}</td>
            <td className="td">{s.kind}</td><td className="td">{s.type}</td><td className="td">{s.scope}</td>
            <td className="td">{s.kind === "temp" ? `TAC → line ${s.span.line}` : `${s.span.line}:${s.span.col}`}</td><td className="td">{s.uses.length}</td>
            <td className="td">{s.initialized ? "yes" : "no"}</td>
          </tr>))}
      </tbody>
    </table>
  );
}
