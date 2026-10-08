"""Explanations ("Why?") built from rule tables; never from ad-hoc strings."""
from typing import Any

from pydantic import BaseModel

from .span import Span


class Explanation(BaseModel):
    rule_id: str
    title: str
    reason: str
    detail: dict[str, Any] = {}
    origin: list[str]
    span: Span | None = None


def explain(rules: dict[str, dict], rule_id: str, origin: list[str], span: Span | None,
            detail: dict[str, Any] | None = None, **fmt: Any) -> Explanation:
    """Look up `rule_id` in `rules` and fill its reason template."""
    r = rules[rule_id]
    return Explanation(rule_id=rule_id, title=r["title"], reason=r["reason_template"].format(**fmt),
                       detail={"concept": r["concept"], **(detail or {})}, origin=origin, span=span)
