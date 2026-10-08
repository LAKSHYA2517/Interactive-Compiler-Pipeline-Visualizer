import { useStore } from "../state/store";
import { Empty, useHl } from "../components/common";

export default function TokensPanel() {
  const { response, select } = useStore();
  const hl = useHl();
  if (!response?.tokens) return <Empty>No tokens yet.</Empty>;
  return (
    <table className="w-full text-sm">
      <thead><tr><th className="th">#</th><th className="th">Type</th><th className="th">Lexeme</th><th className="th">Line:Col</th><th className="th">Id</th></tr></thead>
      <tbody>
        {response.tokens.map((t, i) => (
          <tr key={t.id} onClick={() => select([t.id])} className={`cursor-pointer ${hl(t.id) ? "hl-row" : ""}`}>
            <td className="td text-slate-400">{i}</td><td className="td">{t.type}</td>
            <td className="td font-mono">{t.lexeme || "∅"}</td><td className="td">{t.span.line}:{t.span.col}</td>
            <td className="td font-mono text-xs text-slate-400">{t.id}</td>
          </tr>))}
      </tbody>
    </table>
  );
}
