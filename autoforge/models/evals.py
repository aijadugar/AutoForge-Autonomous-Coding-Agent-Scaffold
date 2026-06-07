from datetime import UTC, datetime
from typing import Any
from uuid import uuid4

from pydantic import BaseModel, Field


class EvalRun(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid4()))
    name: str
    task_goal: str
    task_success: bool
    tool_accuracy: float
    plan_completion: float
    execution_time_ms: float
    cost_estimate_usd: float
    notes: str = ""
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    metadata: dict[str, Any] = Field(default_factory=dict)


class EvalReport(BaseModel):
    runs: list[EvalRun]
    average_tool_accuracy: float
    average_plan_completion: float
    success_rate: float
