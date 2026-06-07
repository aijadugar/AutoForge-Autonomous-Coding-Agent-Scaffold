import ast
from pathlib import Path

from pydantic import BaseModel

from .common import GenericOutput, PathInput, TextInput, TextOutput, safe_path
from .registry import register_tool


class PatchReviewInput(BaseModel):
    patch: str
    test_output: str = ""


@register_tool("quality", description="Parse Python file for syntax errors")
def python_syntax_check(inp: PathInput) -> GenericOutput:
    path = safe_path(inp.path)
    ast.parse(path.read_text(encoding="utf-8"))
    return GenericOutput(message="syntax ok", data={"path": str(path)})


@register_tool("quality", description="Review a patch for obvious risks")
def review_patch(inp: PatchReviewInput) -> GenericOutput:
    risks = []
    if "except Exception" in inp.patch:
        risks.append("broad exception handling")
    if "shell=True" in inp.patch:
        risks.append("shell execution requires input validation")
    return GenericOutput(message="review complete", data={"risks": risks, "tests_seen": bool(inp.test_output)})


@register_tool("quality", description="Check whether text contains TODO markers")
def todo_scan(inp: TextInput) -> GenericOutput:
    todos = [line for line in inp.text.splitlines() if "TODO" in line or "FIXME" in line]
    return GenericOutput(message="scan complete", data={"todos": todos, "count": len(todos)})


@register_tool("quality", description="Estimate maintainability of a text artifact")
def maintainability_score(inp: TextInput) -> GenericOutput:
    lines = max(1, len(inp.text.splitlines()))
    score = max(0, 100 - lines // 5 - inp.text.count("if ") - inp.text.count("for "))
    return GenericOutput(message="scored", data={"score": score})


@register_tool("quality", description="Generate release note from a change summary")
def release_note(inp: TextInput) -> TextOutput:
    return TextOutput(text=f"Change summary: {inp.text.strip()}")


@register_tool("quality", description="Detect large files in a directory")
def large_file_scan(inp: PathInput) -> GenericOutput:
    root = safe_path(inp.path)
    files = [{"path": str(path), "size": path.stat().st_size} for path in Path(root).rglob("*") if path.is_file()]
    largest = sorted(files, key=lambda item: item["size"], reverse=True)[:10]
    return GenericOutput(message="scan complete", data={"largest": largest})

