import { Background, Controls, Edge, Node, ReactFlow } from "@xyflow/react";
import { useMemo } from "react";
import { layout } from "../lib/layout";
import { Empty } from "../components/common";
import { useStore } from "../state/store";
import type { AstNode } from "../types";

const label = (n: AstNode) =>
  n.kind === "Literal" ? n.value : n.kind === "Var" ? n.name : n.kind === "Decl" ? `Decl ${n.var_type} ${n.name}`
    : n.kind === "Assign" ? `Assign ${n.name}` : n.operator ? `${n.kind} ${n.operator}` : n.kind;

export default function AstPanel() {
  const { response, selection, select } = useStore();
  const ast = response?.ast;
  const { nodes, edges } = useMemo(() => {
    const ns: Node[] = [], es: Edge[] = [];
    const go = (n: AstNode) => {
      ns.push({ id: n.id, position: { x: 0, y: 0 }, data: { label: `${label(n)}${n.type ? " : " + n.type : ""}` }, draggable: false });
      n.children.forEach((c) => { es.push({ id: `${n.id}-${c.id}`, source: n.id, target: c.id }); go(c); });
    };
    if (ast) go(ast);
    return { nodes: layout(ns, es, "TB", 120, 36, 20), edges: es };
  }, [ast]);
  if (!ast) return <Empty>No AST.</Empty>;
  const err = new Set<string>(); (function f(n: AstNode) { if (n.error) err.add(n.id); n.children.forEach(f); })(ast);
  const styled = nodes.map((n) => ({
    ...n, style: {
      width: 120, fontSize: 11, padding: 4, borderRadius: 6, textAlign: "center" as const,
      border: err.has(n.id) ? "2px solid #ef4444" : selection.has(n.id) ? "2px solid #6366f1" : "1px solid #94a3b8",
      background: selection.has(n.id) ? "rgba(99,102,241,.25)" : err.has(n.id) ? "rgba(239,68,68,.12)" : "var(--color-white, #fff)",
      color: "#0f172a",
    },
  }));
  return (
    <div className="h-full min-h-[400px]">
      <ReactFlow nodes={styled} edges={edges} fitView nodesConnectable={false} onNodeClick={(_, n) => select([n.id])} minZoom={0.1}>
        <Background /><Controls showInteractive={false} />
      </ReactFlow>
    </div>
  );
}
