import json
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from backend.api.main import app
from backend.api.pipeline import compile_source
from backend.api.schemas import CompileResponse
from backend.optimizer.rules import RULES as OPT_RULES
from backend.parser.ast import walk
from backend.parser.rules import RULES as SYN_RULES
from backend.semantic.rules import RULES as SEM_RULES

GOLD = json.loads((Path(__file__).parent / "golden" / "programs.json").read_text())
client = TestClient(app)


def by_id(r):
    m = {t.id: t for t in r.tokens or []}
    for n in walk(r.ast) if r.ast else []:
        m[n.id] = n
    for coll in (r.symbols, r.tac, r.optimized.tac if r.optimized else [], r.optimized.applied if r.optimized else []):
        for x in coll or []:
            m[x.id] = x
    for a in r.optimized.applied if r.optimized else []:
        if a.instr:
            m[a.instr.id] = a.instr
    return m


def reaches_token(m, i, seen=()):
    x = m[i]
    if x.id.startswith("tok_"):
        return True
    return any(reaches_token(m, o) for o in x.origin if o in m) if hasattr(x, "origin") else False


@pytest.mark.parametrize("name", GOLD)
def test_invariants(name):
    src = GOLD[name]
    r = compile_source(src, True)
    m = by_id(r)
    spans = [x.span for x in m.values() if hasattr(x, "span")]
    assert all(0 <= s.start <= s.end <= len(src) for s in spans if s)
    assert all(i.span.end > i.span.start for i in (r.tac or []) + (r.optimized.tac if r.optimized else []))
    for i in (r.tac or []) + (r.optimized.tac if r.optimized else []):
        assert i.origin and reaches_token(m, i.id), i
    for d in r.diagnostics:
        assert d.explanation.rule_id in {**SEM_RULES, **SYN_RULES}
        assert d.span.end <= len(src)
    for a in (r.optimized.applied if r.optimized else []):
        assert a.explanation.rule_id in OPT_RULES and a.explanation.origin
    CompileResponse.model_validate(json.loads(r.model_dump_json()))
    assert r.model_dump_json() == compile_source(src, True).model_dump_json()


def test_golden_results():
    assert compile_source(GOLD["demo"], True).optimized.tac[-1].text == "print 50"
    for k, rule in [("undeclared", "SEM_UNDECLARED"), ("mismatch", "SEM_TYPE_MISMATCH"),
                    ("redeclared", "SEM_REDECLARED"), ("cond", "SEM_COND_NOT_BOOL"), ("syntax", "SYN_UNEXPECTED_TOKEN")]:
        r = compile_source(GOLD[k], True)
        assert [d.explanation.rule_id for d in r.diagnostics] == [rule] and not r.ok and r.tac is None
    r = compile_source(GOLD["fold_alg"], True)
    assert {a.rule_id for a in r.optimized.applied} >= {"OPT_CONST_FOLD", "OPT_ALGEBRAIC"}


def test_endpoints():
    s = {"source": GOLD["demo"]}
    assert len(client.post("/tokenize", json=s).json()["tokens"]) == 25
    assert client.post("/parse", json=s).json()["ast"]["kind"] == "Program"
    assert client.post("/semantic-analysis", json=s).json()["symbols"][0]["name"] == "a"
    assert len(client.post("/generate-ir", json=s).json()["tac"]) == 6
    assert len(client.post("/optimize", json=s).json()["after"]) == 4
    assert client.post("/compile", json={**s, "optimize": True}).json()["ok"] is True
    d = client.post("/build-dfa", json={"regex": "[a-zA-Z][a-zA-Z0-9]*", "test_input": "Lakshya123"}).json()
    assert d["accepted"] is True
    assert client.post("/build-dfa", json={"regex": "(a"}).status_code == 422


def test_tier2_endpoints():
    r = client.post("/parse", json={"source": GOLD["demo"]}).json()
    assert r["slr"]["accepted"] and r["table"]["conflicts"] == []
    g = client.post("/grammar/analyze", json={"grammar_text": "E -> E + T | T\nT -> id", "test_input": "id + id"}).json()
    assert g["run"]["accepted"] and g["follow"]["E"] == ["$", "+"]
    assert client.post("/grammar/analyze", json={"grammar_text": "nope"}).status_code == 422
