from pathlib import Path

from autoforge.models import ToolCall
from autoforge.tools import get_registry


def test_registry_has_required_tool_count():
    specs = get_registry().list_specs()
    assert len(specs) >= 50
    namespaces = {spec.namespace for spec in specs}
    assert {"filesystem", "git", "research", "execution", "planning"}.issubset(namespaces)


def test_tool_composition_search_read_plan(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    Path("pkg").mkdir()
    Path("pkg/example.py").write_text("def hello():\n    return 'world'\n", encoding="utf-8")

    registry = get_registry()
    search = registry.execute(ToolCall(tool="filesystem.search_files", arguments={"pattern": "*.py", "root": "."}))
    assert search.ok
    first = search.output["items"][0]

    read = registry.execute(ToolCall(tool="filesystem.read_file", arguments={"path": first}))
    assert "hello" in read.output["text"]

    plan = registry.execute(
        ToolCall(
            tool="planning.decompose_task",
            arguments={"goal": "change hello", "context": read.output["text"]},
        )
    )
    assert plan.ok
    assert plan.output["data"]["steps"]

