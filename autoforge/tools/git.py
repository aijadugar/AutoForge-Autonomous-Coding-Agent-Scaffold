import subprocess

from pydantic import BaseModel

from .common import CommandInput, TextOutput, safe_path
from .registry import register_tool


class GitCommitInput(BaseModel):
    message: str


class GitCheckoutInput(BaseModel):
    ref: str


class GitBranchInput(BaseModel):
    name: str | None = None


def _git(args: list[str], timeout: int = 30) -> TextOutput:
    proc = subprocess.run(["git", *args], cwd=str(safe_path(".")), text=True, capture_output=True, timeout=timeout)
    return TextOutput(text=(proc.stdout + proc.stderr).strip(), metadata={"returncode": proc.returncode, "args": args})


@register_tool("git", description="Show git status")
def git_status(inp: CommandInput) -> TextOutput:
    return _git(["status", "--short"], inp.timeout_seconds)


@register_tool("git", description="Show git diff")
def git_diff(inp: CommandInput) -> TextOutput:
    args = ["diff"] + ([inp.command] if inp.command else [])
    return _git(args, inp.timeout_seconds)


@register_tool("git", description="Create a git commit", risk="high")
def git_commit(inp: GitCommitInput) -> TextOutput:
    return _git(["commit", "-am", inp.message])


@register_tool("git", description="List or create branches", risk="medium")
def git_branch(inp: GitBranchInput) -> TextOutput:
    return _git(["branch", inp.name] if inp.name else ["branch", "--show-current"])


@register_tool("git", description="Show git log")
def git_log(inp: CommandInput) -> TextOutput:
    return _git(["log", "--oneline", "-n", inp.command or "5"], inp.timeout_seconds)


@register_tool("git", description="Checkout a git ref", risk="high")
def git_checkout(inp: GitCheckoutInput) -> TextOutput:
    return _git(["checkout", inp.ref])


@register_tool("git", description="Show staged diff")
def git_diff_cached(inp: CommandInput) -> TextOutput:
    return _git(["diff", "--cached"], inp.timeout_seconds)


@register_tool("git", description="Add files to index", risk="medium")
def git_add(inp: CommandInput) -> TextOutput:
    return _git(["add", inp.command or "."], inp.timeout_seconds)


@register_tool("git", description="Show current HEAD SHA")
def git_rev_parse(inp: CommandInput) -> TextOutput:
    return _git(["rev-parse", inp.command or "HEAD"], inp.timeout_seconds)


@register_tool("git", description="Show file changes by name")
def git_changed_files(inp: CommandInput) -> TextOutput:
    return _git(["diff", "--name-only", inp.command] if inp.command else ["diff", "--name-only"], inp.timeout_seconds)


@register_tool("git", description="Show blame for a file")
def git_blame(inp: CommandInput) -> TextOutput:
    return _git(["blame", inp.command], inp.timeout_seconds)

