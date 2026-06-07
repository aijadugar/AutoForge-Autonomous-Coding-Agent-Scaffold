from autoforge.memory import MemoryManager
from autoforge.models import AgentContext, StepStatus, ToolCall, ToolResult
from autoforge.persistence import SQLiteStore
from autoforge.tools import ToolRegistry


class Executor:
    """Executes plans while preserving state across long tool chains."""

    def __init__(self, registry: ToolRegistry, memory: MemoryManager, store: SQLiteStore | None = None) -> None:
        self.registry = registry
        self.memory = memory
        self.store = store

    def execute_tool(self, context: AgentContext, tool: str, arguments: dict) -> ToolResult:
        call = ToolCall(tool=tool, arguments=arguments)
        execution = self.registry.execute_recorded(call, task_id=context.task_id)
        context.tool_outputs.append(execution.result)
        self.memory.remember(context.memory_namespace, "tool_result", execution.result.model_dump())
        if self.store:
            self.store.save_tool_execution(context.task_id, execution)
            self.store.add_trace(
                context.task_id,
                "tool_execution",
                {"tool": tool, "ok": execution.result.ok, "elapsed_ms": execution.result.elapsed_ms},
            )
        return execution.result

    def compress_context(self, context: AgentContext) -> None:
        completed = []
        if context.active_plan:
            completed = [step.title for step in context.active_plan.steps if step.status == StepStatus.completed]
        recent_outputs = [
            {"tool": result.tool, "ok": result.ok, "summary": str(result.output or result.error)[:180]}
            for result in context.tool_outputs[-8:]
        ]
        context.compressed_summary = (
            f"Completed steps: {', '.join(completed) or 'none'}\n"
            f"Recent outputs: {recent_outputs}\n"
            f"Memory: {self.memory.summarize(context.memory_namespace, limit=8)}"
        )
        if context.active_plan:
            context.active_plan.compressed_context = context.compressed_summary

