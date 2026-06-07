from autoforge.agent import AgentRuntime
from autoforge.memory import MemoryManager
from autoforge.persistence import SQLiteStore
from autoforge.subagents import SubAgentTool
from autoforge.subagents.tool import InvokeSubAgentInput
from autoforge.tools import get_registry


def test_runtime_executes_long_horizon_workflow(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    store = SQLiteStore(f"sqlite:///{tmp_path / 'autoforge.db'}")
    result = AgentRuntime(store).submit("Inspect this repo and produce a verified plan")

    assert result.success
    assert result.plan.completion_ratio() == 1.0
    assert len(result.tool_results) >= 20
    assert "Completed" in result.summary
    assert store.list_traces(result.task_id)


def test_subagents_have_independent_memory(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    memory = MemoryManager()
    parent = __import__("autoforge.models", fromlist=["AgentContext"]).AgentContext(
        task_id="task-1",
        objective="review code",
        memory_namespace="parent",
    )
    tool = SubAgentTool(get_registry(), memory)
    response = tool.invoke(InvokeSubAgentInput(agent="research", objective="FastAPI", context="ctx"), parent)

    assert response.agent == "research"
    assert memory.recall("parent/research", "handoff")
    assert not memory.recall("parent/code", "handoff")

