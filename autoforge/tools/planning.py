from pydantic import BaseModel, Field

from autoforge.models import PlanStep, TaskPlan

from .common import GenericOutput, TextInput, TextOutput
from .registry import register_tool


class PlanInput(BaseModel):
    goal: str
    context: str = ""


class ComplexityInput(BaseModel):
    goal: str
    files_touched: int = 0
    unknowns: int = 0


class PlanOutput(BaseModel):
    plan: dict


@register_tool("planning", description="Create a task plan")
def create_plan(inp: PlanInput) -> PlanOutput:
    steps = [
        PlanStep(title="Understand repository", description="Inspect files, dependencies, and conventions"),
        PlanStep(title="Design change", description="Choose minimal architecture and tool chain"),
        PlanStep(title="Implement change", description="Apply code edits with typed outputs"),
        PlanStep(title="Verify change", description="Run tests and review outputs"),
    ]
    plan = TaskPlan(goal=inp.goal, steps=steps)
    return PlanOutput(plan=plan.model_dump())


@register_tool("planning", description="Decompose a task into candidate steps")
def decompose_task(inp: PlanInput) -> GenericOutput:
    verbs = ["inspect", "design", "implement", "test", "review"]
    return GenericOutput(message="decomposed", data={"steps": [f"{verb}: {inp.goal}" for verb in verbs]})


@register_tool("planning", description="Summarize context for compression")
def summarize_context(inp: TextInput) -> TextOutput:
    text = inp.text.strip()
    return TextOutput(text=text[:500] + ("..." if len(text) > 500 else ""))


@register_tool("planning", description="Estimate task complexity")
def estimate_complexity(inp: ComplexityInput) -> GenericOutput:
    score = min(10, 1 + inp.files_touched + inp.unknowns * 2 + len(inp.goal) // 80)
    return GenericOutput(message="estimated", data={"score": score, "band": "high" if score >= 7 else "medium" if score >= 4 else "low"})


@register_tool("planning", description="Prioritize plan steps")
def prioritize_steps(inp: PlanInput) -> GenericOutput:
    return GenericOutput(message="prioritized", data={"order": ["risk discovery", "smallest code path", "verification"]})


@register_tool("planning", description="Identify dependencies between steps")
def identify_dependencies(inp: PlanInput) -> GenericOutput:
    return GenericOutput(message="dependencies identified", data={"dependencies": [{"before": "inspect", "after": "implement"}]})


@register_tool("planning", description="Track plan progress")
def track_progress(inp: PlanInput) -> GenericOutput:
    return GenericOutput(message="tracked", data={"goal": inp.goal, "progress": 0.0})


@register_tool("planning", description="Compress completed plan context")
def compress_context(inp: TextInput) -> TextOutput:
    lines = [line for line in inp.text.splitlines() if line.strip()]
    return TextOutput(text=" | ".join(lines[-10:]))


@register_tool("planning", description="Select the next action")
def select_next_action(inp: PlanInput) -> TextOutput:
    return TextOutput(text="inspect_repository", metadata={"goal": inp.goal})

