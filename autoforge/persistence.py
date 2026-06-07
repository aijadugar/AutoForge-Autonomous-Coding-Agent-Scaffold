import json
import sqlite3
from contextlib import contextmanager
from datetime import UTC, datetime
from pathlib import Path
from typing import Iterator

from .models import EvalRun, TaskPlan, TaskRecord, TaskStatus, ToolExecution


def _db_path(database_url: str) -> Path:
    if not database_url.startswith("sqlite:///"):
        raise ValueError("AutoForge currently supports sqlite:/// URLs only")
    return Path(database_url.removeprefix("sqlite:///")).resolve()


class SQLiteStore:
    """Small repository around SQLite.

    JSON columns keep early schemas flexible while the service boundaries settle.
    """

    def __init__(self, database_url: str) -> None:
        self.path = _db_path(database_url)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.init()

    @contextmanager
    def connect(self) -> Iterator[sqlite3.Connection]:
        conn = sqlite3.connect(self.path)
        conn.row_factory = sqlite3.Row
        try:
            yield conn
            conn.commit()
        finally:
            conn.close()

    def init(self) -> None:
        with self.connect() as conn:
            conn.executescript(
                """
                CREATE TABLE IF NOT EXISTS tasks (
                  id TEXT PRIMARY KEY,
                  goal TEXT NOT NULL,
                  status TEXT NOT NULL,
                  plan_id TEXT,
                  result_json TEXT NOT NULL,
                  created_at TEXT NOT NULL,
                  updated_at TEXT NOT NULL
                );
                CREATE TABLE IF NOT EXISTS plans (
                  id TEXT PRIMARY KEY,
                  task_id TEXT,
                  payload_json TEXT NOT NULL,
                  updated_at TEXT NOT NULL
                );
                CREATE TABLE IF NOT EXISTS tool_executions (
                  id TEXT PRIMARY KEY,
                  task_id TEXT,
                  payload_json TEXT NOT NULL,
                  created_at TEXT NOT NULL
                );
                CREATE TABLE IF NOT EXISTS agent_traces (
                  id INTEGER PRIMARY KEY AUTOINCREMENT,
                  task_id TEXT,
                  event_type TEXT NOT NULL,
                  payload_json TEXT NOT NULL,
                  created_at TEXT NOT NULL
                );
                CREATE TABLE IF NOT EXISTS evaluations (
                  id TEXT PRIMARY KEY,
                  payload_json TEXT NOT NULL,
                  created_at TEXT NOT NULL
                );
                """
            )

    def save_task(self, task: TaskRecord) -> TaskRecord:
        task.updated_at = datetime.now(UTC)
        with self.connect() as conn:
            conn.execute(
                """
                INSERT INTO tasks VALUES (?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(id) DO UPDATE SET
                  goal=excluded.goal,
                  status=excluded.status,
                  plan_id=excluded.plan_id,
                  result_json=excluded.result_json,
                  updated_at=excluded.updated_at
                """,
                (
                    task.id,
                    task.goal,
                    task.status.value,
                    task.plan_id,
                    json.dumps(task.result),
                    task.created_at.isoformat(),
                    task.updated_at.isoformat(),
                ),
            )
        return task

    def get_task(self, task_id: str) -> TaskRecord | None:
        with self.connect() as conn:
            row = conn.execute("SELECT * FROM tasks WHERE id = ?", (task_id,)).fetchone()
        if row is None:
            return None
        return TaskRecord(
            id=row["id"],
            goal=row["goal"],
            status=TaskStatus(row["status"]),
            plan_id=row["plan_id"],
            result=json.loads(row["result_json"]),
            created_at=datetime.fromisoformat(row["created_at"]),
            updated_at=datetime.fromisoformat(row["updated_at"]),
        )

    def save_plan(self, task_id: str, plan: TaskPlan) -> TaskPlan:
        with self.connect() as conn:
            conn.execute(
                """
                INSERT INTO plans VALUES (?, ?, ?, ?)
                ON CONFLICT(id) DO UPDATE SET payload_json=excluded.payload_json, updated_at=excluded.updated_at
                """,
                (plan.id, task_id, plan.model_dump_json(), datetime.now(UTC).isoformat()),
            )
        return plan

    def get_plan(self, plan_id: str) -> TaskPlan | None:
        with self.connect() as conn:
            row = conn.execute("SELECT payload_json FROM plans WHERE id = ?", (plan_id,)).fetchone()
        return TaskPlan.model_validate_json(row["payload_json"]) if row else None

    def save_tool_execution(self, task_id: str | None, execution: ToolExecution) -> None:
        with self.connect() as conn:
            conn.execute(
                "INSERT INTO tool_executions VALUES (?, ?, ?, ?)",
                (execution.id, task_id, execution.model_dump_json(), execution.created_at.isoformat()),
            )

    def add_trace(self, task_id: str | None, event_type: str, payload: dict) -> None:
        with self.connect() as conn:
            conn.execute(
                "INSERT INTO agent_traces(task_id, event_type, payload_json, created_at) VALUES (?, ?, ?, ?)",
                (task_id, event_type, json.dumps(payload), datetime.now(UTC).isoformat()),
            )

    def list_traces(self, task_id: str | None = None) -> list[dict]:
        query = "SELECT * FROM agent_traces"
        params: tuple[str, ...] = ()
        if task_id:
            query += " WHERE task_id = ?"
            params = (task_id,)
        with self.connect() as conn:
            rows = conn.execute(query + " ORDER BY id", params).fetchall()
        return [
            {
                "id": row["id"],
                "task_id": row["task_id"],
                "event_type": row["event_type"],
                "payload": json.loads(row["payload_json"]),
                "created_at": row["created_at"],
            }
            for row in rows
        ]

    def save_eval(self, run: EvalRun) -> EvalRun:
        with self.connect() as conn:
            conn.execute(
                "INSERT OR REPLACE INTO evaluations VALUES (?, ?, ?)",
                (run.id, run.model_dump_json(), run.created_at.isoformat()),
            )
        return run

    def list_evals(self) -> list[EvalRun]:
        with self.connect() as conn:
            rows = conn.execute("SELECT payload_json FROM evaluations ORDER BY created_at DESC").fetchall()
        return [EvalRun.model_validate_json(row["payload_json"]) for row in rows]
