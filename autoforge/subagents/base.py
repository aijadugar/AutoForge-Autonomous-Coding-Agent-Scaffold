from pydantic import BaseModel, Field

from autoforge.memory import MemoryManager
from autoforge.models import AgentContext, ToolCall, ToolResult
from autoforge.tools import ToolRegistry


class SubAgentRequest(BaseModel):
    objective: str
    context: str = ""


class SubAgentResponse(BaseModel):
    agent: str
    objective: str
    findings: list[str] = Field(default_factory=list)
    artifacts: dict = Field(default_factory=dict)
    tool_results: list[dict] = Field(default_factory=list)


class BaseSubAgent:
    name = "base"
    allowed_tools: tuple[str, ...] = ()

    def __init__(self, registry: ToolRegistry, memory: MemoryManager) -> None:
        self.registry = registry
        self.memory = memory

    def run(self, request: SubAgentRequest, parent_context: AgentContext) -> SubAgentResponse:
        namespace = f"{parent_context.memory_namespace}/{self.name}"
        context = AgentContext(
            task_id=parent_context.task_id,
            objective=request.objective,
            memory_namespace=namespace,
            compressed_summary=request.context,
        )
        results = self._work(request, context)
        self.memory.remember(namespace, "handoff", results.model_dump())
        return results

    def call_tool(self, context: AgentContext, tool: str, arguments: dict) -> ToolResult:
        if tool not in self.allowed_tools:
            raise PermissionError(f"{self.name} cannot use {tool}")
        result = self.registry.execute(ToolCall(tool=tool, arguments=arguments))
        context.tool_outputs.append(result)
        self.memory.remember(context.memory_namespace, "tool_result", result.model_dump())
        return result

    def _work(self, request: SubAgentRequest, context: AgentContext) -> SubAgentResponse:
        raise NotImplementedError


class ResearchAgent(BaseSubAgent):
    name = "research"
    allowed_tools = ("research.web_search", "research.dependency_lookup", "research.github_search")

    def _work(self, request: SubAgentRequest, context: AgentContext) -> SubAgentResponse:
        results = [self.call_tool(context, "research.web_search", {"query": request.objective, "limit": 2})]
        return SubAgentResponse(
            agent=self.name,
            objective=request.objective,
            findings=["Identified relevant external research adapters and dependency lookup points."],
            artifacts={"research_summary": request.context[:240]},
            tool_results=[result.model_dump() for result in results],
        )


class CodeAgent(BaseSubAgent):
    name = "code"
    allowed_tools = ("filesystem.search_files", "filesystem.read_file", "planning.decompose_task")

    def _work(self, request: SubAgentRequest, context: AgentContext) -> SubAgentResponse:
        results = [self.call_tool(context, "planning.decompose_task", {"goal": request.objective, "context": request.context})]
        return SubAgentResponse(
            agent=self.name,
            objective=request.objective,
            findings=["Produced implementation decomposition suitable for executor composition."],
            artifacts={"change_strategy": "small, typed modules with tests"},
            tool_results=[result.model_dump() for result in results],
        )


class TestingAgent(BaseSubAgent):
    name = "testing"
    allowed_tools = ("execution.run_pytest", "quality.python_syntax_check")

    def _work(self, request: SubAgentRequest, context: AgentContext) -> SubAgentResponse:
        return SubAgentResponse(
            agent=self.name,
            objective=request.objective,
            findings=["Verification should include unit, integration, API, and workflow tests."],
            artifacts={"test_command": "pytest --cov=autoforge"},
        )


class ReviewAgent(BaseSubAgent):
    name = "review"
    allowed_tools = ("quality.review_patch", "quality.maintainability_score")

    def _work(self, request: SubAgentRequest, context: AgentContext) -> SubAgentResponse:
        result = self.call_tool(context, "quality.maintainability_score", {"text": request.context})
        return SubAgentResponse(
            agent=self.name,
            objective=request.objective,
            findings=["Review should prioritize behavioral risk, verification gaps, and operational safety."],
            artifacts={"risk_posture": "moderate"},
            tool_results=[result.model_dump()],
        )
