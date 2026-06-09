from autoforge.llm.planner import generate_plan
from autoforge.models import PlanStep, TaskPlan


class Planner:

    def create(self, goal: str, context_summary: str = "") -> TaskPlan:

        plan_json = generate_plan(
            goal=goal,
            context=context_summary,
        )

        steps = [
            PlanStep(
                title=item["title"],
                description=item["description"],
            )
            for item in plan_json
        ]

        for idx in range(1, len(steps)):
            steps[idx].dependencies.append(steps[idx - 1].id)

        return TaskPlan(
            goal=goal,
            steps=steps,
            compressed_context=context_summary,
        )