# CareerPath («همراه شغلی»)

Persian-first job-search companion for software job seekers in Iran, built for Quera BuildX (Problem #2). Each user picks one career path; an agent learns their real background and preferences, explains which real listings fit and why, revises the search and the resume from feedback, and prepares a Persian or English resume in which every claim is traced to the user's own evidence.

| Item | Value |
|---|---|
| Live URL | TODO(T-105) |
| Status | Planning v2 complete; build starts at gates G1–G4 |
| Hosting | Frankfurt VPS (Docker Compose + Caddy) |
| LLM | OpenRouter, total budget $5 |
| Team | 2 people: A = Agent & Data, B = Platform & Delivery |

## Documentation

| File | Purpose |
|---|---|
| [`CLAUDE.md`](CLAUDE.md) | Operating rules for Claude Code sessions |
| [`docs/COMPETITION.md`](docs/COMPETITION.md) | Hard rules and deliverables (overrides everything) |
| [`docs/PRODUCT.md`](docs/PRODUCT.md) | Scope, golden path, agent decision points, honesty rule |
| [`docs/ACCEPTANCE.md`](docs/ACCEPTANCE.md) | Pass/fail criteria, fixtures, golden E2E script |
| [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md) | Stack, schemas, matching, agent graphs, security, deployment |
| [`docs/TASKS.md`](docs/TASKS.md) | Day map, slices, owners, checkpoints |
| [`docs/DECISIONS.md`](docs/DECISIONS.md) | Decision log, rejected ideas, open items |
| [`docs/SUBMISSION.md`](docs/SUBMISSION.md) | Business plan, pitch, video and technical-doc plan (Persian) |
| [`docs/diagrams/architecture.svg`](docs/diagrams/architecture.svg) | Topology and agent graphs |

## Quick start

TODO(T-101): prerequisites, environment setup from `.env.example`, run, test.

## Stack

Python 3.12 · FastAPI · Jinja2 + HTMX · PostgreSQL 16 · SQLAlchemy 2 + Alembic · Pydantic v2 · LangGraph (Postgres checkpointer) · OpenRouter via the OpenAI SDK · batch scraper (httpx).
