import { Empty, useHl } from "../components/common";
import { useStore } from "../state/store";

/** Target assembly; every instruction links back to the TAC line it was generated from. */
export default function AsmPanel() {
  const { response, select } = useStore();
  const hl = useHl();
  const asm = response?.asm;
  if (!asm) return <Empty>No assembly: fix the errors first.</Empty>;
  const text = asm.map((l) => (l.kind === "instr" ? "    " : "") + l.text).join("\n") + "\n";
  const download = () => {
    const a = document.createElement("a");
    a.href = URL.createObjectURL(new Blob([text], { type: "text/plain" }));
    a.download = "program.asm";
    a.click();
  };
  return (
    <div>
      <div className="flex items-center gap-2 border-b border-slate-200 p-2 text-xs text-slate-500 dark:border-slate-800">
        <span>generated from {response.asm_from === "optimized" ? "optimized TAC" : "unoptimized TAC"}</span>
        <button className="btn-ghost ml-auto" onClick={() => navigator.clipboard?.writeText(text)}>Copy</button>
        <button className="btn-ghost" onClick={download}>Download .asm</button>
      </div>
      <ol className="font-mono text-sm">
        {asm.map((l, n) => (
          <li key={l.id} onClick={() => select([l.id])}
            className={`flex cursor-pointer gap-3 px-3 py-0.5 ${hl(l.id) ? "hl-row" : "hover:bg-slate-100 dark:hover:bg-slate-900"}`}>
            <span className="w-6 text-right text-slate-400">{n + 1}</span>
            <span className={`w-44 ${l.kind === "directive" ? "text-purple-600 dark:text-purple-400" : l.kind === "label" ? "font-semibold text-accent" : "pl-4"}`}>{l.text}</span>
            <span className="text-slate-400">{l.comment && `; ${l.comment}`}</span>
          </li>))}
      </ol>
    </div>
  );
}
