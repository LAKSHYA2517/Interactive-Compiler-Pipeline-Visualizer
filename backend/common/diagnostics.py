from typing import Literal

from pydantic import BaseModel

from .explain import Explanation
from .span import Span


class Diagnostic(BaseModel):
    id: str
    severity: Literal["error", "warning"]
    phase: Literal["lexer", "parser", "semantic"]
    message: str
    span: Span
    origin: list[str]
    explanation: Explanation
