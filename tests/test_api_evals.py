from fastapi.testclient import TestClient

from autoforge.api.app import create_app
from autoforge.config import get_settings
from autoforge.evals import EvalHarness
from autoforge.persistence import SQLiteStore


def test_api_task_tools_health(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    get_settings.cache_clear()
    monkeypatch.setenv("AUTOFORGE_DATABASE_URL", f"sqlite:///{tmp_path / 'api.db'}")
    client = TestClient(create_app())

    health = client.get("/health")
    assert health.status_code == 200
    assert health.json()["ok"] is True

    tools = client.get("/tools")
    assert tools.status_code == 200
    assert tools.json()["count"] >= 50

    created = client.post("/task", json={"goal": "Run a minimal workflow"})
    assert created.status_code == 200
    task_id = created.json()["task_id"]

    status = client.post(f"/task/{task_id}/status")
    assert status.status_code == 200
    assert status.json()["task"]["status"] == "succeeded"


def test_eval_harness_records_report(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    store = SQLiteStore(f"sqlite:///{tmp_path / 'evals.db'}")
    harness = EvalHarness(store)
    run = harness.run("smoke", "Evaluate the workflow")
    report = harness.report()

    assert run.task_success
    assert report.success_rate == 1.0
    assert report.average_plan_completion == 1.0

