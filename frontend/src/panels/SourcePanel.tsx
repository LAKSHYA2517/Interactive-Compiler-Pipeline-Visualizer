import { useStore } from "../state/store";
import { useHl, Empty } from "../components/common";

const COLOR: Record<string, string> = {
  KEYWORD: "text-purple-600 dark:text-purple-400", IDENTIFIER: "", INT_LIT: "text-emerald-600", FLOAT_LIT: "text-emerald-600",
  OPERATOR: "text-orange-600", DELIMITER: "text-slate-500",
};

/** Source text rendered token by token; every token is clickable. */
export default function SourcePanel() {
  const { response, select, source } = useStore();
  const hl = useHl();
  if (!response?.tokens) return <Empty>Compile to see the source split into tokens.</Empty>;
  const parts: JSX.Element[] = [];
  let pos = 0;
  for (const t of response.tokens) {
    if (t.span.start > pos) parts.push(<span key={"g" + pos}>{source.slice(pos, t.span.start)}</span>);
    parts.push(
      <span key={t.id} onClick={() => select([t.id])} title={`${t.type} ${t.id}`}
        className={`cursor-pointer rounded ${COLOR[t.type] ?? ""} ${hl(t.id) ? "hl-row" : "hover:bg-slate-200 dark:hover:bg-slate-800"}`}>{t.lexeme}</span>);
    pos = t.span.end;
  }
  return <pre className="p-4 font-mono text-sm leading-6">{parts}</pre>;
}
