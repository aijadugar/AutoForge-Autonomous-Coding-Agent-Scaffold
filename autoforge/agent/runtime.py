import time

from autoforge.memory import MemoryManager
from autoforge.models import AgentContext, AgentResult, StepStatus, TaskRecord, TaskStatus
from autoforge.persistence import SQLiteStore
from autoforge.planner import Planner
from autoforge.subagents import SubAgentTool
from autoforge.subagents.tool import InvokeSubAgentInput
from autoforge.tools import ToolRegistry, get_registry

from autoforge.executor import Executor


class AgentRuntime:
    """Coordinates planning, tool execution, subagent delegation, and persistence."""

    def __init__(
        self,
        store: SQLiteStore,
        registry: ToolRegistry | None = None,
        memory: MemoryManager | None = None,
        planner: Planner | None = None,
    ) -> None:
        self.store = store
        self.registry = registry or get_registry()
        self.memory = memory or MemoryManager()
        self.planner = planner or Planner()
        self.executor = Executor(self.registry, self.memory, self.store)
        self.subagents = SubAgentTool(self.registry, self.memory)

    def submit(self, goal: str) -> AgentResult:
        started = time.perf_counter()
        task = self.store.save_task(TaskRecord(goal=goal, status=TaskStatus.running))
        context = AgentContext(task_id=task.id, objective=goal, memory_namespace=f"task:{task.id}")
        context.active_plan = self.planner.create(goal)
        task.plan_id = context.active_plan.id
        self.store.save_plan(task.id, context.active_plan)
        self.store.add_trace(task.id, "task_started", {"goal": goal})

        try:
            self._run_workflow(context)
            context.active_plan.status = StepStatus.completed
            task.status = TaskStatus.succeeded
            summary = self._summary(context)
            task.result = {"summary": summary, "elapsed_ms": (time.perf_counter() - started) * 1000}
            self.store.save_plan(task.id, context.active_plan)
            self.store.save_task(task)
            self.store.add_trace(task.id, "task_succeeded", task.result)
            return AgentResult(task_id=task.id, success=True, plan=context.active_plan, summary=summary, tool_results=context.tool_outputs)
        except Exception as exc:
            task.status = TaskStatus.failed
            task.result = {"error": str(exc)}
            if context.active_plan:
                context.active_plan.status = StepStatus.failed
                self.store.save_plan(task.id, context.active_plan)
            self.store.save_task(task)
            self.store.add_trace(task.id, "task_failed", {"error": str(exc)})
            raise

    def _run_workflow(self, context: AgentContext) -> None:
        assert context.active_plan is not None
        tool_sequence = [
            ("filesystem.list_directory", {"path": "."}),
            ("filesystem.search_files", {"pattern": "*.py", "root": "."}),
            ("planning.decompose_task", {"goal": context.objective, "context": ""}),
            ("planning.estimate_complexity", {"goal": context.objective, "files_touched": 3, "unknowns": 2}),
            ("planning.identify_dependencies", {"goal": context.objective, "context": ""}),
            ("planning.prioritize_steps", {"goal": context.objective, "context": ""}),
            ("research.package_search", {"query": "fastapi pydantic autonomous agent", "limit": 2}),
            ("research.github_search", {"query": "agent tool registry pydantic", "limit": 2}),
            ("research.security_advisory_lookup", {"package": "fastapi", "ecosystem": "python"}),
            ("quality.todo_scan", {"text": context.objective}),
            ("quality.maintainability_score", {"text": context.objective}),
            ("planning.select_next_action", {"goal": context.objective, "context": context.compressed_summary}),
            ("execution.environment_info", {"command": "", "cwd": ".", "timeout_seconds": 5}),
            ("git.git_status", {"command": "", "cwd": ".", "timeout_seconds": 5}),
            ("planning.summarize_context", {"text": context.compressed_summary}),
            ("planning.compress_context", {"text": context.compressed_summary}),
            ("filesystem.workspace_root", {"path": "."}),
            ("research.dependency_lookup", {"package": "pydantic-settings", "ecosystem": "python"}),
            ("quality.release_note", {"text": "AutoForge runtime workflow completed"}),
            ("planning.track_progress", {"goal": context.objective, "context": context.compressed_summary}),
            ("filesystem.search_files", {"pattern": "README.md", "root": "."}),
        ]
        step_index = 0
        for index, (tool, args) in enumerate(tool_sequence):
            if step_index < len(context.active_plan.steps):
                step = context.active_plan.steps[step_index]
                step.status = StepStatus.running
                result = self.executor.execute_tool(context, tool, args)
                step.tool_calls.append(result.call_id)
                step.results[tool] = {"ok": result.ok, "output": result.output, "error": result.error}
                if (index + 1) % 3 == 0:
                    step.status = StepStatus.completed
                    step_index += 1
            else:
                self.executor.execute_tool(context, tool, args)
            if (index + 1) % 5 == 0:
                self.executor.compress_context(context)
                self.store.save_plan(context.task_id or "", context.active_plan)

        for agent_name in ["research", "code", "testing", "review"]:
            response = self.subagents.invoke(
                inp=InvokeSubAgentInput(
                    agent=agent_name,
                    objective=context.objective,
                    context=context.compressed_summary,
                ),
                parent_context=context,
            )
            self.memory.remember(context.memory_namespace, f"subagent:{agent_name}", response.model_dump())
            self.store.add_trace(context.task_id, "subagent_handoff", response.model_dump())

        for step in context.active_plan.steps:
            if step.status in {StepStatus.pending, StepStatus.running}:
                step.status = StepStatus.completed
        self.executor.compress_context(context)

    def _summary(self, context: AgentContext) -> str:
        ok = sum(1 for result in context.tool_outputs if result.ok)
        failed = len(context.tool_outputs) - ok
        subagent_handoffs = len([item for item in self.memory.recall(context.memory_namespace) if isinstance(item, dict)])
        return f"Completed {ok} tool calls with {failed} failures and {subagent_handoffs} memory handoffs."
