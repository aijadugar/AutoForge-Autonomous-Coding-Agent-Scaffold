import subprocess
import time

from pydantic import BaseModel

from .common import CommandInput, GenericOutput, TextOutput, safe_path
from .registry import register_tool


class PythonInput(BaseModel):
    code: str
    timeout_seconds: int = 10


class BenchmarkInput(BaseModel):
    command: str
    iterations: int = 3


def _run(command: list[str] | str, cwd: str | None, timeout: int, shell: bool = False) -> TextOutput:
    proc = subprocess.run(
        command,
        cwd=str(safe_path(cwd or ".")),
        timeout=timeout,
        shell=shell,
        text=True,
        capture_output=True,
    )
    return TextOutput(
        text=(proc.stdout + proc.stderr).strip(),
        metadata={"returncode": proc.returncode, "command": command if isinstance(command, str) else " ".join(command)},
    )


@register_tool("execution", description="Run a shell command", risk="high")
def run_shell(inp: CommandInput) -> TextOutput:
    return _run(inp.command, inp.cwd, inp.timeout_seconds, shell=True)


@register_tool("execution", description="Run inline Python code", risk="high")
def run_python(inp: PythonInput) -> TextOutput:
    return _run(["python", "-c", inp.code], None, inp.timeout_seconds)


@register_tool("execution", description="Run pytest", risk="medium")
def run_pytest(inp: CommandInput) -> TextOutput:
    args = inp.command or "pytest"
    return _run(args, inp.cwd, inp.timeout_seconds, shell=True)


@register_tool("execution", description="Run mypy", risk="medium")
def run_mypy(inp: CommandInput) -> TextOutput:
    return _run(inp.command or "python -m mypy .", inp.cwd, inp.timeout_seconds, shell=True)


@register_tool("execution", description="Run linter", risk="medium")
def run_linter(inp: CommandInput) -> TextOutput:
    return _run(inp.command or "python -m ruff check .", inp.cwd, inp.timeout_seconds, shell=True)


@register_tool("execution", description="Run formatter check", risk="medium")
def run_formatter(inp: CommandInput) -> TextOutput:
    return _run(inp.command or "python -m black --check .", inp.cwd, inp.timeout_seconds, shell=True)


@register_tool("execution", description="Run benchmark command repeatedly", risk="medium")
def run_benchmark(inp: BenchmarkInput) -> GenericOutput:
    timings = []
    for _ in range(inp.iterations):
        started = time.perf_counter()
        subprocess.run(inp.command, shell=True, cwd=str(safe_path(".")), capture_output=True, text=True, timeout=60)
        timings.append((time.perf_counter() - started) * 1000)
    return GenericOutput(message="benchmark complete", data={"iterations": inp.iterations, "timings_ms": timings})


@register_tool("execution", description="Check command availability")
def which_command(inp: CommandInput) -> TextOutput:
    return _run(f"where {inp.command}", inp.cwd, inp.timeout_seconds, shell=True)


@register_tool("execution", description="Capture environment details")
def environment_info(inp: CommandInput) -> GenericOutput:
    return GenericOutput(message="ok", data={"cwd": str(safe_path(inp.cwd or ".")), "timeout": inp.timeout_seconds})

