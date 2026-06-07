from fastapi import Depends, FastAPI, HTTPException
from pydantic import BaseModel

from autoforge.agent import AgentRuntime
from autoforge.config import Settings, get_settings
from autoforge.evals import EvalHarness
from autoforge.persistence import SQLiteStore
from autoforge.telemetry import configure_logging, setup_tracing
from autoforge.tools import get_registry


class TaskRequest(BaseModel):
    goal: str


class TaskResponse(BaseModel):
    task_id: str
    success: bool
    summary: str
    plan: dict


def get_store(settings: Settings = Depends(get_settings)) -> SQLiteStore:
    return SQLiteStore(settings.database_url)


def create_app() -> FastAPI:
    settings = get_settings()
    configure_logging(settings.log_level)
    setup_tracing("autoforge-api")
    app = FastAPI(title="AutoForge", version="0.1.0")

    @app.get("/health")
    def health() -> dict:
        return {"ok": True, "environment": settings.environment}

    @app.post("/task", response_model=TaskResponse)
    def submit_task(request: TaskRequest, store: SQLiteStore = Depends(get_store)) -> TaskResponse:
        runtime = AgentRuntime(store=store)
        result = runtime.submit(request.goal)
        return TaskResponse(
            task_id=result.task_id,
            success=result.success,
            summary=result.summary,
            plan=result.plan.model_dump(),
        )

    @app.post("/task/{task_id}/status")
    def task_status(task_id: str, store: SQLiteStore = Depends(get_store)) -> dict:
        task = store.get_task(task_id)
        if not task:
            raise HTTPException(status_code=404, detail="task not found")
        plan = store.get_plan(task.plan_id) if task.plan_id else None
        return {"task": task.model_dump(), "plan": plan.model_dump() if plan else None}

    @app.get("/tools")
    def tools() -> dict:
        specs = [spec.model_dump() | {"qualified_name": spec.qualified_name} for spec in get_registry().list_specs()]
        return {"count": len(specs), "tools": specs}

    @app.get("/evals")
    def evals(store: SQLiteStore = Depends(get_store)) -> dict:
        harness = EvalHarness(store)
        return harness.report().model_dump()

    return app


app = create_app()

