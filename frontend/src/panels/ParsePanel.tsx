import { useEffect, useState } from "react";
import { parseSlr } from "../api/client";
import { Empty } from "../components/common";
import SlrView from "../components/SlrView";
import { useStore } from "../state/store";
import type { ParseResponse } from "../types";

/** SLR(1) trace for the current source (tier 2). */
export default function ParsePanel() {
  const { response, source } = useStore();
  const [res, setRes] = useState<ParseResponse | null>(null);
  const [err, setErr] = useState<string | null>(null);
  useEffect(() => {
    if (!response) return;
    parseSlr(source).then((r) => { setRes(r); setErr(null); }).catch((e) => setErr(String(e)));
  }, [response]); // eslint-disable-line
  if (err) return <Empty>{err}</Empty>;
  if (!res?.table) return <Empty>Compile to see the SLR(1) parse trace.</Empty>;
  return <SlrView table={res.table} run={res.slr} />;
}
