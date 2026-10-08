import { Background, Controls, Edge, Node, ReactFlow } from "@xyflow/react";
import { useMemo } from "react";
import { Empty } from "../components/common";
import { basicBlocks } from "../lib/lineage";
import { layout } from "../lib/layout";
import { useStore } from "../state/store";

/** Control-flow graph of the (optimized, if present) TAC: one node per basic block. */
export default function CfgPanel() {
  const { response, selection, select } = useStore();
  const tac = response?.optimized?.tac ?? response?.tac;
  const { nodes, edges } = useMemo(() => {
    if (!tac) return { nodes: [], edges: [] };
    const blocks = basicBlocks(tac);
    const byLabel = new Map<string, number>();
    blocks.forEach((b, k) => { if (b[0].op === "label") byLabel.set(b[0].label!, k); });
    const es: Edge[] = [];
    blocks.forEach((b, k) => {
      const last = b[b.length - 1];
      if (last.op === "goto") es.push({ id: `${k}g`, source: `B${k}`, target: `B${byLabel.get(last.label!)}` });
      else {
        if (last.op === "if_goto") es.push({ id: `${k}t`, source: `B${k}`, target: `B${byLabel.get(last.label!)}`, label: "true" });
        if (k + 1 < blocks.length) es.push({ id: `${k}f`, source: `B${k}`, target: `B${k + 1}` });
      }
    });
    const ns: Node[] = blocks.map((b, k) => ({ id: `B${k}`, position: { x: 0, y: 0 }, data: { label: b.map((i) => i.text).join("\n"), ids: b.map((i) => i.id) } }));
    return { nodes: layout(ns, es, "TB", 170, 20 + 18 * Math.max(...blocks.map((b) => b.length)), 30), edges: es };
  }, [tac]);
  if (!tac) return <Empty>No TAC to graph.</Empty>;
  const styled = nodes.map((n) => ({
    ...n, style: {
      width: 170, whiteSpace: "pre" as const, fontFamily: "monospace", fontSize: 11, textAlign: "left" as const, color: "#0f172a",
      border: (n.data.ids as string[]).some((i) => selection.has(i)) ? "2px solid #6366f1" : "1px solid #94a3b8",
    },
  }));
  return (
    <div className="h-full min-h-[400px]">
      <ReactFlow nodes={styled} edges={edges} fitView nodesConnectable={false} onNodeClick={(_, n) => select(n.data.ids as string[])}>
        <Background /><Controls showInteractive={false} />
      </ReactFlow>
    </div>
  );
}
