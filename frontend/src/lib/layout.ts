import dagre from "@dagrejs/dagre";
import type { Edge, Node } from "@xyflow/react";

/** Position nodes with dagre. `dir`: TB for trees, LR for automata. */
export function layout(nodes: Node[], edges: Edge[], dir: "TB" | "LR", w = 110, h = 36, sep = 30): Node[] {
  const g = new dagre.graphlib.Graph();
  g.setGraph({ rankdir: dir, nodesep: sep, ranksep: sep + 20 });
  g.setDefaultEdgeLabel(() => ({}));
  nodes.forEach((n) => g.setNode(n.id, { width: w, height: h }));
  edges.forEach((e) => { if (e.source !== e.target) g.setEdge(e.source, e.target); });
  dagre.layout(g);
  return nodes.map((n) => { const p = g.node(n.id); return { ...n, position: { x: p.x - w / 2, y: p.y - h / 2 } }; });
}
