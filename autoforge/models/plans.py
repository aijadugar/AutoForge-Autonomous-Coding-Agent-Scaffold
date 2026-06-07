from enum import StrEnum
from typing import Any
from uuid import uuid4

from pydantic import BaseModel, Field


class StepStatus(StrEnum):
    pending = "pending"
    running = "running"
    blocked = "blocked"
    completed = "completed"
    failed = "failed"


class PlanStep(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid4()))
    title: str
    description: str = ""
    status: StepStatus = StepStatus.pending
    dependencies: list[str] = Field(default_factory=list)
    tool_calls: list[str] = Field(default_factory=list)
    results: dict[str, Any] = Field(default_factory=dict)


class TaskPlan(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid4()))
    goal: str
    steps: list[PlanStep] = Field(default_factory=list)
    status: StepStatus = StepStatus.pending
    compressed_context: str = ""

    def ready_steps(self) -> list[PlanStep]:
        completed = {step.id for step in self.steps if step.status == StepStatus.completed}
        return [
            step
            for step in self.steps
            if step.status == StepStatus.pending and all(dep in completed for dep in step.dependencies)
        ]

    def completion_ratio(self) -> float:
        if not self.steps:
            return 0.0
        done = sum(1 for step in self.steps if step.status == StepStatus.completed)
        return done / len(self.steps)

