import MonacoEditor, { OnMount } from "@monaco-editor/react";
import { useEffect, useRef } from "react";
import { smallestNodeAt, spansOf } from "../lib/lineage";
import { useStore } from "../state/store";
import type { Span } from "../types";

export default function Editor({ dark }: { dark: boolean }) {
  const { source, setSource, response, selection, lineage, reveal } = useStore();
  const ed = useRef<Parameters<OnMount>[0] | null>(null);
  const mo = useRef<Parameters<OnMount>[1] | null>(null);
  const deco = useRef<ReturnType<Parameters<OnMount>[0]["createDecorationsCollection"]> | null>(null);
  const live = useRef({ response, source });
  live.current = { response, source };

  const range = (s: Span) => {
    const m = ed.current!.getModel()!;
    const a = m.getPositionAt(s.start), b = m.getPositionAt(s.end);
    return { startLineNumber: a.lineNumber, startColumn: a.column, endLineNumber: b.lineNumber, endColumn: b.column };
  };

  const onMount: OnMount = (editor, monaco) => {
    ed.current = editor; mo.current = monaco;
    deco.current = editor.createDecorationsCollection([]);
    editor.onMouseDown((e) => {
      const m = editor.getModel(); const pos = e.target.position;
      if (!m || !pos || !live.current.response?.ast) return;
      const id = smallestNodeAt(live.current.response.ast, m.getOffsetAt(pos));
      if (id) useStore.getState().select([id]);
    });
  };

  // selection -> decorations
  useEffect(() => {
    if (!ed.current || !deco.current || !ed.current.getModel()) return;
    if (response && response.source !== source) { deco.current.set([]); return; }   // stale spans
    deco.current.set(spansOf(lineage, selection).map((s) => ({ range: range(s), options: { inlineClassName: "hl-src" } })));
  }, [selection, lineage, source]); // eslint-disable-line

  // diagnostics -> markers
  useEffect(() => {
    if (!ed.current || !mo.current) return;
    const m = ed.current.getModel()!;
    const stale = response && response.source !== source;
    mo.current.editor.setModelMarkers(m, "minilang", stale ? [] : (response?.diagnostics ?? []).map((d) => {
      const r = range(d.span.end > d.span.start ? d.span : { ...d.span, end: d.span.end + 1 });
      return { ...r, message: d.message, severity: d.severity === "error" ? mo.current!.MarkerSeverity.Error : mo.current!.MarkerSeverity.Warning };
    }));
  }, [response, source]);

  useEffect(() => {
    if (reveal && ed.current) ed.current.revealRangeInCenterIfOutsideViewport(range(reveal.span));
  }, [reveal]); // eslint-disable-line

  return (
    <MonacoEditor height="100%" defaultLanguage="plaintext" theme={dark ? "vs-dark" : "light"} value={source}
      onChange={(v) => setSource(v ?? "")} onMount={onMount}
      options={{ minimap: { enabled: false }, fontSize: 14, scrollBeyondLastLine: false, automaticLayout: true }} />
  );
}
