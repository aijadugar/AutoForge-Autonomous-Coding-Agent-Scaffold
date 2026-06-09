import time

from autoforge.memory import MemoryManager
from autoforge.models import AgentContext, AgentResult, StepStatus, TaskRecord, TaskStatus
from autoforge.persistence import SQLiteStore
from autoforge.planner import Planner
from autoforge.subagents import SubAgentTool
from autoforge.subagents.tool import InvokeSubAgentInput
from autoforge.tools import ToolRegistry, get_registry
from autoforge.executor import Executor
from autoforge.llm.agent import AgentBrain


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
        self.agent = AgentBrain()

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

        for iteration in range(20):

            action = self.agent.choose_action(
                goal=context.objective,
                memory=context.compressed_summary,
                tools=self.registry.list_specs(),
            )

            action_type = action.get("type")

            if action_type == "tool":

                result = self.executor.execute_tool(
                    context,
                    action["tool"],
                    action.get("args", {}),
                )

                self.memory.remember(
                    context.memory_namespace,
                    f"tool:{action['tool']}",
                    result.model_dump(),
                )

                self.store.add_trace(
                    context.task_id,
                    "tool_execution",
                    result.model_dump(),
                )

            elif action_type == "subagent":

                response = self.subagents.invoke(
                    InvokeSubAgentInput(
                        agent=action["agent"],
                        objective=context.objective,
                        context=context.compressed_summary,
                    ),
                    context,
                )

                self.memory.remember(
                    context.memory_namespace,
                    f"subagent:{action['agent']}",
                    response.model_dump(),
                )

            elif action_type == "finish":

                break

            self.executor.compress_context(context)

        for step in context.active_plan.steps:
            step.status = StepStatus.completed
    
    def _summary(self, context: AgentContext) -> str:
        ok = sum(1 for result in context.tool_outputs if result.ok)
        failed = len(context.tool_outputs) - ok
        subagent_handoffs = len([item for item in self.memory.recall(context.memory_namespace) if isinstance(item, dict)])
        return f"Completed {ok} tool calls with {failed} failures and {subagent_handoffs} memory handoffs."
