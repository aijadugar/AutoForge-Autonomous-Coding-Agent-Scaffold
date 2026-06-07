from typing import Any
from uuid import uuid4

from pydantic import BaseModel, Field

from .plans import TaskPlan
from .tools import ToolResult


class AgentContext(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid4()))
    task_id: str | None = None
    objective: str
    memory_namespace: str = "root"
    active_plan: TaskPlan | None = None
    tool_outputs: list[ToolResult] = Field(default_factory=list)
    compressed_summary: str = ""
    metadata: dict[str, Any] = Field(default_factory=dict)


class AgentResult(BaseModel):
    task_id: str
    success: bool
    plan: TaskPlan
    summary: str
    tool_results: list[ToolResult] = Field(default_factory=list)

