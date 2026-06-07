from autoforge.models import PlanStep, TaskPlan


class Planner:
    """Creates explicit, durable plans from a goal and repository context."""

    def create(self, goal: str, context_summary: str = "") -> TaskPlan:
        steps = [
            PlanStep(title="Map repository", description="List files and identify project conventions"),
            PlanStep(title="Research constraints", description="Check dependencies, docs, and relevant prior art"),
            PlanStep(title="Design implementation", description="Decompose goal into tool-composable work units"),
            PlanStep(title="Delegate specialized work", description="Ask subagents for research, code, test, and review outputs"),
            PlanStep(title="Apply changes", description="Use tool outputs to produce repository modifications"),
            PlanStep(title="Run verification", description="Execute unit, integration, and workflow tests"),
            PlanStep(title="Review risk", description="Analyze patch, tests, and remaining operational risks"),
            PlanStep(title="Summarize delivery", description="Persist traces, update task state, and produce final summary"),
        ]
        for idx, step in enumerate(steps):
            if idx > 0:
                step.dependencies.append(steps[idx - 1].id)
        return TaskPlan(goal=goal, steps=steps, compressed_context=context_summary)

