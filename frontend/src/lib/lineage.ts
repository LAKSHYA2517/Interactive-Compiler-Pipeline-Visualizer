import type { AstNode, CompileResponse, Instr, Span } from "../types";

/** Anything clickable carries id + origin (+ span). */
export interface Item { id: string; origin: string[]; span?: Span | null; kind: string; ref: any }

export interface Lineage {
  byId: Map<string, Item>;
  /** reverse index of `origin`: id -> ids that list it as an origin */
  children: Map<string, string[]>;
  /** AST node id -> child AST ids (a node's subtree counts as part of what it is made of) */
  astKids: Map<string, string[]>;
  expand(id: string): Set<string>;
}

function walk(n: AstNode, f: (n: AstNode) => void) { f(n); n.children.forEach((c) => walk(c, f)); }

export function buildLineage(r: CompileResponse | null): Lineage {
  const byId = new Map<string, Item>();
  const children = new Map<string, string[]>();
  const astKids = new Map<string, string[]>();
  const add = (kind: string, ref: any, origin: string[]) =>
    byId.set(ref.id, { id: ref.id, origin, span: ref.span, kind, ref });
  if (r) {
    r.tokens?.forEach((t) => add("token", t, []));
    if (r.ast) walk(r.ast, (n) => { add("ast", n, n.origin); astKids.set(n.id, n.children.map((c) => c.id)); });
    r.symbols?.forEach((s) => add("symbol", s, s.origin));
    r.diagnostics.forEach((d) => add("diagnostic", d, d.origin));
    r.tac?.forEach((i) => add("tac", i, i.origin));
    r.optimized?.tac.forEach((i) => add("opt", i, i.origin));
    r.asm?.forEach((a) => add("asm", a, a.origin));
    r.optimized?.applied.forEach((a) => {
      if (a.instr && !byId.has(a.instr.id)) add("opt", a.instr, a.instr.origin);
      add("applied", { ...a, span: a.explanation.span }, [...a.before, ...(a.after ? [a.after] : [])]);
    });
  }
  byId.forEach((it) => it.origin.forEach((o) => {
    const l = children.get(o);
    if (l) l.push(it.id); else children.set(o, [it.id]);
  }));

  const closure = (seeds: Iterable<string>, next: (id: string) => string[]) => {
    const seen = new Set<string>(); const work = [...seeds];
    while (work.length) {
      const id = work.pop()!;
      if (seen.has(id)) continue;
      seen.add(id);
      work.push(...next(id));
    }
    return seen;
  };
  const up = (id: string) => closure([id], (x) => [...(byId.get(x)?.origin ?? []), ...(astKids.get(x) ?? [])].filter((o) => byId.has(o)));
  const down = (seeds: string[]) => closure(seeds, (x) => children.get(x) ?? []);

  return {
    byId, children, astKids,
    expand(id) {
      const ups = up(id);
      const seeds = [id, ...[...ups].filter((x) => byId.get(x)?.kind !== "token")];
      const out = new Set<string>([...ups, ...down(seeds)]);
      // dependents' own origins (e.g. an optimized line's TAC source and tokens)
      for (const x of [...out]) if (byId.get(x)?.kind === "opt" || byId.get(x)?.kind === "applied") up(x).forEach((y) => out.add(y));
      return out;
    },
  };
}

/** Smallest AST node whose span contains the character offset. */
export function smallestNodeAt(ast: AstNode | null, offset: number): string | null {
  let best: AstNode | null = null;
  if (ast) walk(ast, (n) => {
    if (n.span.start <= offset && offset < n.span.end && (!best || n.span.end - n.span.start <= best.span.end - best.span.start)) best = n;
  });
  return best ? (best as AstNode).id : null;
}

export function spansOf(lin: Lineage, ids: Set<string>): Span[] {
  const out: Span[] = [];
  ids.forEach((id) => { const s = lin.byId.get(id)?.span; if (s && s.end > s.start && lin.byId.get(id)?.kind !== "applied") out.push(s); });
  return out;
}

/** Basic blocks (leader rule from the brief) for the CFG panel. */
export function basicBlocks(tac: Instr[]): Instr[][] {
  const blocks: Instr[][] = []; let prevJump = true;
  for (const i of tac) {
    if (prevJump || i.op === "label") blocks.push([]);
    blocks[blocks.length - 1].push(i);
    prevJump = i.op === "goto" || i.op === "if_goto";
  }
  return blocks;
}
