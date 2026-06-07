import time

from autoforge.agent import AgentRuntime
from autoforge.models import EvalReport, EvalRun
from autoforge.persistence import SQLiteStore


class EvalHarness:
    """Runs lightweight evaluations against the real runtime."""

    def __init__(self, store: SQLiteStore) -> None:
        self.store = store

    def run(self, name: str, task_goal: str) -> EvalRun:
        started = time.perf_counter()
        runtime = AgentRuntime(self.store)
        result = runtime.submit(task_goal)
        elapsed_ms = (time.perf_counter() - started) * 1000
        ok_tools = sum(1 for item in result.tool_results if item.ok)
        total_tools = max(1, len(result.tool_results))
        run = EvalRun(
            name=name,
            task_goal=task_goal,
            task_success=result.success,
            tool_accuracy=ok_tools / total_tools,
            plan_completion=result.plan.completion_ratio(),
            execution_time_ms=elapsed_ms,
            cost_estimate_usd=round(total_tools * 0.0002, 4),
            notes=result.summary,
            metadata={"task_id": result.task_id, "tool_calls": total_tools},
        )
        return self.store.save_eval(run)

    def report(self) -> EvalReport:
        runs = self.store.list_evals()
        if not runs:
            return EvalReport(runs=[], average_tool_accuracy=0, average_plan_completion=0, success_rate=0)
        return EvalReport(
            runs=runs,
            average_tool_accuracy=sum(run.tool_accuracy for run in runs) / len(runs),
            average_plan_completion=sum(run.plan_completion for run in runs) / len(runs),
            success_rate=sum(1 for run in runs if run.task_success) / len(runs),
        )

