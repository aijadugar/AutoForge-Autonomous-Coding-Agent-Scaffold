from datetime import UTC, datetime
from typing import Any
from uuid import uuid4

from pydantic import BaseModel, Field


class ToolSpec(BaseModel):
    name: str
    namespace: str
    description: str
    input_model: str
    output_model: str
    risk: str = "low"

    @property
    def qualified_name(self) -> str:
        return f"{self.namespace}.{self.name}"


class ToolCall(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid4()))
    tool: str
    arguments: dict[str, Any] = Field(default_factory=dict)
    parent_call_id: str | None = None


class ToolResult(BaseModel):
    call_id: str
    tool: str
    ok: bool
    output: Any = None
    error: str | None = None
    elapsed_ms: float = 0.0


class ToolExecution(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid4()))
    task_id: str | None = None
    call: ToolCall
    result: ToolResult
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
