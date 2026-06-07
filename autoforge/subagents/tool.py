from pydantic import BaseModel

from autoforge.memory import MemoryManager
from autoforge.models import AgentContext
from autoforge.tools import ToolRegistry, register_tool

from .base import CodeAgent, ResearchAgent, ReviewAgent, SubAgentRequest, SubAgentResponse, TestingAgent


class InvokeSubAgentInput(BaseModel):
    agent: str
    objective: str
    context: str = ""


class InvokeSubAgentOutput(BaseModel):
    response: dict


class SubAgentTool:
    """Parent-facing facade that preserves subagent isolation."""

    def __init__(self, registry: ToolRegistry, memory: MemoryManager) -> None:
        self.registry = registry
        self.memory = memory
        self.agents = {
            "research": ResearchAgent(registry, memory),
            "code": CodeAgent(registry, memory),
            "testing": TestingAgent(registry, memory),
            "review": ReviewAgent(registry, memory),
        }

    def invoke(self, inp: InvokeSubAgentInput, parent_context: AgentContext) -> SubAgentResponse:
        agent = self.agents[inp.agent]
        return agent.run(SubAgentRequest(objective=inp.objective, context=inp.context), parent_context)


@register_tool("subagents", description="Describe available isolated subagents")
def list_subagents(inp: InvokeSubAgentInput) -> InvokeSubAgentOutput:
    return InvokeSubAgentOutput(
        response={
            "requested": inp.agent,
            "available": ["research", "code", "testing", "review"],
            "note": "Runtime uses SubAgentTool.invoke for parent-child communication.",
        }
    )

