# AutoForge Engineering Memo

## What Was Built

AutoForge is a deployable FastAPI service scaffold for autonomous coding workflows. It includes a typed agent runtime, dynamic tool registry with 50+ tools across six namespaces, a durable planner/executor loop, isolated subagents, namespaced memory, SQLite persistence, structured logging, OpenTelemetry tracing, metrics, retry wrappers, an evaluation harness, sample artifacts, and tests.

## What Was Intentionally Cut

The research tools are provider adapters rather than live internet clients. That keeps the system deterministic, testable, and safe without pretending that production credentials, rate limits, compliance rules, and source quality policies do not matter. The code editor is represented by composable filesystem and planning tools rather than an AST patch engine, which would be the next major investment.

## What Additional Time Would Improve

More time should go into a real patch planner/editor, async task queues, Postgres migrations, distributed tracing export, provider-backed research integrations, policy controls for risky tools, richer eval fixtures, and coverage around failure recovery. The subagents would also benefit from explicit budget accounting and stronger typed handoff schemas per role.

## Design Decision

The tool registry uses decorator-based self-registration instead of a central router. The alternative would be a large dispatcher mapping tool names to functions. A dispatcher is easy at first, but it becomes a coordination hotspot as teams add namespaces. Decorators keep the extension point next to the implementation while preserving a single registry for introspection, rate limiting, tracing, and execution.

