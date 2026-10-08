import { Background, BaseEdge, Controls, Edge, EdgeProps, getBezierPath, Handle, Node, NodeProps, Position, ReactFlow } from "@xyflow/react";
import { useMemo } from "react";
import { layout } from "../lib/layout";

interface Props {
  states: string[]; start: string; accept: string[];
  transitions: { from: string; to: string; symbol: string }[];
  active?: string | null; activeEdge?: { from: string; to: string } | null;
}

function StateNode({ id, data }: NodeProps) {
  const d = data as { accept: boolean; start: boolean; active: boolean };
  return (
    <div className={`flex h-9 w-9 items-center justify-center rounded-full text-[10px] text-slate-900 ${d.active ? "bg-accent/40" : "bg-white"}`}
      style={{ border: d.accept ? "4px double #475569" : "1.5px solid #475569", boxShadow: d.active ? "0 0 0 3px #6366f1" : undefined }}>
      {d.start && <span className="absolute -left-4 text-slate-500">▶</span>}
      <Handle type="target" position={Position.Left} style={{ opacity: 0 }} />
      {id}
      <Handle type="source" position={Position.Right} style={{ opacity: 0 }} />
    </div>
  );
}

function LoopEdge({ sourceX, sourceY, targetX, targetY, label, style, markerEnd }: EdgeProps) {
  const path = `M ${sourceX} ${sourceY} C ${sourceX + 30} ${sourceY - 60}, ${targetX - 30} ${targetY - 60}, ${targetX} ${targetY}`;
  return (
    <>
      <BaseEdge path={path} style={style} markerEnd={markerEnd} />
      <text x={(sourceX + targetX) / 2} y={sourceY - 40} textAnchor="middle" fontSize={10} fill="currentColor">{label as string}</text>
    </>
  );
}

function PlainEdge(p: EdgeProps) {
  const [path, lx, ly] = getBezierPath(p);
  return (
    <>
      <BaseEdge path={path} style={p.style} markerEnd={p.markerEnd} />
      <text x={lx} y={ly - 4} textAnchor="middle" fontSize={10} fill="currentColor">{p.label as string}</text>
    </>
  );
}

const nodeTypes = { state: StateNode };
const edgeTypes = { loop: LoopEdge, plain: PlainEdge };

/** NFA/DFA drawing: circles, double circle for accept, merged labelled edges. */
export default function Automaton({ states, start, accept, transitions, active, activeEdge }: Props) {
  const { nodes, edges } = useMemo(() => {
    const merged = new Map<string, string[]>();
    transitions.forEach((t) => { const k = `${t.from}>${t.to}`; merged.set(k, [...(merged.get(k) ?? []), t.symbol]); });
    const es: Edge[] = [...merged].map(([k, syms]) => {
      const [from, to] = k.split(">");
      return { id: k, source: from, target: to, label: [...new Set(syms)].join(", "), type: from === to ? "loop" : "plain", markerEnd: { type: "arrowclosed" as const } };
    });
    const ns: Node[] = states.map((s) => ({ id: s, type: "state", position: { x: 0, y: 0 }, data: {}, draggable: false }));
    return { nodes: layout(ns, es, "LR", 40, 40, 50), edges: es };
  }, [states, transitions]);
  const ns = nodes.map((n) => ({ ...n, data: { accept: accept.includes(n.id), start: n.id === start, active: n.id === active } }));
  const es = edges.map((e) => {
    const on = activeEdge && e.source === activeEdge.from && e.target === activeEdge.to;
    return { ...e, animated: !!on, style: { stroke: on ? "#6366f1" : "#94a3b8", strokeWidth: on ? 3 : 1.5 } };
  });
  return (
    <ReactFlow nodes={ns} edges={es} nodeTypes={nodeTypes} edgeTypes={edgeTypes} fitView nodesConnectable={false} minZoom={0.2}>
      <Background /><Controls showInteractive={false} />
    </ReactFlow>
  );
}
