# AutoForge

AutoForge is a production-oriented scaffold for an autonomous coding agent service. It is not a toy chatbot: the codebase has a FastAPI API, a durable runtime, dynamic tool registration, isolated subagents, a planner/executor split, SQLite persistence, structured logging, OpenTelemetry traces, metrics, retry wrappers, and an evaluation harness.

## Quick Start 

```bash
python -m venv .venv
.\.venv\Scripts\activate
pip install -e ".[dev]"
pytest --cov=autoforge
uvicorn autoforge.api.app:app --reload
```

Submit a task:

```bash
curl -X POST http://127.0.0.1:8000/task \
  -H "Content-Type: application/json" \
  -d '{"goal":"find all FastAPI routes in this repository"}'
```

## Architecture

```text
autoforge/
  api/          FastAPI app and HTTP models
  agent/        Runtime orchestration
  memory/       Namespaced memory manager
  planner/      TaskPlan creation
  executor/     Tool execution and context compression
  tools/        Dynamic tool registry and 50+ tools
  subagents/    Research, code, testing, and review agents
  evals/        Evaluation harness and reporting
  telemetry/    logging, metrics, traces
  models/       Pydantic contracts
  tests/        unit, integration, workflow tests
```

## Tool System

Tools self-register with `@register_tool(namespace=...)`. The registry stores the function, Pydantic input model, Pydantic output model, metadata, retry behavior, metrics, and tracing. There is no giant if/else router.

Namespaces included:

- `filesystem`: read/write/search/move/copy/delete/stat/hash/count
- `git`: status/diff/commit/branch/log/checkout/add/blame
- `research`: web, GitHub, Stack Overflow, package, dependency, security adapters
- `execution`: shell, Python, pytest, mypy, linter, formatter, benchmark
- `planning`: plan creation, decomposition, context compression, prioritization
- `quality`: syntax checks, patch review, TODO scan, maintainability, release notes

Research tools are provider adapters by default. They return structured outputs and are ready for approved external providers, but they do not perform unauthenticated scraping in this scaffold.

## Long-Horizon Runtime

The runtime creates a durable `TaskPlan`, executes a chain of more than 20 tool calls, compresses context every few calls, and persists traces to SQLite. Subagents have independent memory namespaces and only receive allowed tools. Parent-child communication flows through `SubAgentTool`.

## API

- `POST /task`
- `POST /task/{id}/status`
- `GET /tools`
- `GET /evals`
- `GET /health`

## Persistence

SQLite stores:

- tasks
- plans
- tool executions
- agent traces
- evaluations

The schema intentionally uses JSON payload columns for early flexibility. A production migration would move hot query fields into first-class relational columns.

## Evaluation

`EvalHarness` runs the real runtime and records:

- task success
- tool accuracy
- plan completion
- execution time
- cost estimate

Example artifacts live in `examples/`.

