import inspect
import time
from collections.abc import Callable
from dataclasses import dataclass
from typing import Any, TypeVar

from pydantic import BaseModel
from tenacity import retry, stop_after_attempt, wait_exponential

from autoforge.exceptions import RateLimitExceeded, ToolExecutionError, ToolNotFoundError
from autoforge.models import ToolCall, ToolExecution, ToolResult, ToolSpec
from autoforge.telemetry import MetricsCollector, get_logger, get_tracer

InputT = TypeVar("InputT", bound=BaseModel)
OutputT = TypeVar("OutputT", bound=BaseModel)


@dataclass(frozen=True)
class RegisteredTool:
    spec: ToolSpec
    input_model: type[BaseModel]
    output_model: type[BaseModel]
    handler: Callable[[BaseModel], BaseModel]


class TokenBucket:
    def __init__(self, per_minute: int) -> None:
        self.per_minute = per_minute
        self.calls: list[float] = []

    def allow(self) -> bool:
        now = time.time()
        window_start = now - 60
        self.calls = [call for call in self.calls if call >= window_start]
        if len(self.calls) >= self.per_minute:
            return False
        self.calls.append(now)
        return True


class ToolRegistry:
    def __init__(self, metrics: MetricsCollector | None = None, rate_limit_per_minute: int = 120) -> None:
        self._tools: dict[str, RegisteredTool] = {}
        self.metrics = metrics or MetricsCollector()
        self.rate_limiter = TokenBucket(rate_limit_per_minute)
        self.log = get_logger("autoforge.tools")
        self.tracer = get_tracer("autoforge.tools")

    def register(
        self,
        namespace: str,
        name: str,
        description: str,
        input_model: type[BaseModel],
        output_model: type[BaseModel],
        risk: str,
        handler: Callable[[BaseModel], BaseModel],
    ) -> None:
        qualified = f"{namespace}.{name}"
        self._tools[qualified] = RegisteredTool(
            spec=ToolSpec(
                namespace=namespace,
                name=name,
                description=description,
                input_model=input_model.__name__,
                output_model=output_model.__name__,
                risk=risk,
            ),
            input_model=input_model,
            output_model=output_model,
            handler=handler,
        )

    def list_specs(self) -> list[ToolSpec]:
        return sorted((tool.spec for tool in self._tools.values()), key=lambda spec: spec.qualified_name)

    def get(self, qualified_name: str) -> RegisteredTool:
        try:
            return self._tools[qualified_name]
        except KeyError as exc:
            raise ToolNotFoundError(f"Tool not registered: {qualified_name}") from exc

    def execute(self, call: ToolCall) -> ToolResult:
        if not self.rate_limiter.allow():
            raise RateLimitExceeded("Tool rate limit exceeded")
        registered = self.get(call.tool)
        started = time.perf_counter()
        with self.tracer.start_as_current_span(f"tool:{call.tool}") as span:
            span.set_attribute("tool.name", call.tool)
            try:
                payload = registered.input_model.model_validate(call.arguments)
                output = _run_with_retry(registered.handler, payload)
                result = ToolResult(
                    call_id=call.id,
                    tool=call.tool,
                    ok=True,
                    output=output.model_dump(),
                    elapsed_ms=(time.perf_counter() - started) * 1000,
                )
                self.metrics.increment("tool.success")
                self.metrics.observe_ms(f"tool.{call.tool}.elapsed_ms", result.elapsed_ms)
                return result
            except Exception as exc:
                elapsed = (time.perf_counter() - started) * 1000
                self.metrics.increment("tool.failure")
                self.log.warning("tool_failed", tool=call.tool, error=str(exc), elapsed_ms=elapsed)
                return ToolResult(call_id=call.id, tool=call.tool, ok=False, error=str(exc), elapsed_ms=elapsed)

    def execute_recorded(self, call: ToolCall, task_id: str | None = None) -> ToolExecution:
        result = self.execute(call)
        return ToolExecution(task_id=task_id, call=call, result=result)


@retry(wait=wait_exponential(multiplier=0.05, min=0.05, max=1), stop=stop_after_attempt(2), reraise=True)
def _run_with_retry(handler: Callable[[BaseModel], BaseModel], payload: BaseModel) -> BaseModel:
    try:
        return handler(payload)
    except Exception as exc:
        raise ToolExecutionError(str(exc)) from exc


_registry = ToolRegistry()


def get_registry() -> ToolRegistry:
    return _registry


def register_tool(namespace: str, name: str | None = None, description: str = "", risk: str = "low"):
    def decorator(func: Callable[[InputT], OutputT]) -> Callable[[InputT], OutputT]:
        sig = inspect.signature(func)
        params = list(sig.parameters.values())
        if len(params) != 1 or params[0].annotation is inspect.Signature.empty:
            raise TypeError("Tools must accept one typed Pydantic input model")
        if sig.return_annotation is inspect.Signature.empty:
            raise TypeError("Tools must declare a Pydantic output model")
        tool_name = name or func.__name__
        get_registry().register(
            namespace=namespace,
            name=tool_name,
            description=description or (func.__doc__ or "").strip(),
            input_model=params[0].annotation,
            output_model=sig.return_annotation,
            risk=risk,
            handler=func,
        )
        return func

    return decorator

