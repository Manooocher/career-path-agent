# CLAUDE.md

CareerPath («همراه شغلی»): a Persian-first, RTL web app for Quera BuildX Problem #2. Each user picks one tech career path; an agent finds and explains fitting real (scraped) listings, revises the search and the resume from user feedback, and prepares an evidence-grounded resume in Persian or English. Team of two; five days; total LLM budget $5 on OpenRouter.

## Docs map (read only what your task needs)

| File | Read when |
|---|---|
| `docs/COMPETITION.md` | Before anything that could touch a hard rule (C-01 … C-10) |
| `docs/PRODUCT.md` | When scope or wording is unclear |
| `docs/ACCEPTANCE.md` | Always: the AC rows your task lists, plus "Fixtures" for anything matching-related |
| `docs/ARCHITECTURE.md` | Only the sections named in your task's **Read** line |
| `docs/TASKS.md` | At session start, to pick and update your task |
| `docs/DECISIONS.md` | Before choosing anything not specified; never act on an [open] item |

## Workflow

1. Open `docs/TASKS.md`. Take the lowest-numbered `[ ]` task for your owner (A or B) whose dependencies are `[x]`. Mark it `[~]` on your branch `t-<id>-<slug>`.
2. Read the task's **Read** sections and AC rows. Write a plan of ≤ 10 lines and wait for approval.
3. Implement with tests in the same change. A task bigger than M (≤ 4 h) is split before continuing.
4. Run lint and tests (see Commands). All green before asking for review.
5. Mark the task `[x]` only when every listed AC passes; list the AC IDs verified in the PR description.
6. Stop and ask when: a decision is missing from the docs (add it to `DECISIONS.md` "Open items"), the change alters scope, a schema differs from ARCHITECTURE "Schemas", or a new dependency is needed.

## Hard rules

- No n8n, agent builders, site builders, or local LLM runtimes (C-03, C-05).
- LLM calls only through `app/llm/`; keys only from environment; prompts only in `app/prompts/` with a `version:` line.
- Matching (filters, scoring, ranking) never calls an LLM.
- Honesty rule (PRODUCT §5): no generated text may state a skill, employer, institution, date or number absent from confirmed evidence. Never add hardcoded demo output outside `tests/`.
- Every user question from the agent is a LangGraph `interrupt` with the Postgres checkpointer; never auto-answer or auto-approve on the user's behalf.
- Every query filters by the session's `user_id`; never trust IDs produced by the model.
- All user-facing text is Persian, in templates; pages are `lang="fa" dir="rtl"`.
- No external CDN. Static assets live in `app/web/static/`.
- Never log prompt bodies, profile text, or secrets.
- Fault injection must stay off in production.
- Scraping only through `app/ingest/` as a batch command: robots.txt, ≥ 3 s between requests, strip phone numbers, emails and names; never call it from a web request; never commit `data/snapshot/`.
- Every LLM call must fit the budget: batch where possible, use the FAST tier unless the task says SMART, never call the live API from tests.

## Commands

**Install (local venv, for editing/tests without Docker)**
```
python3 -m venv .venv && . .venv/bin/activate
pip install -e ".[dev]"
```

**Run locally (full stack: Caddy + app + PostgreSQL 16)**
```
cp .env.example .env   # then set SECRET_KEY (16+ chars) and POSTGRES_PASSWORD
docker compose -f deploy/docker-compose.yml --env-file .env up -d --build
curl http://localhost/healthz   # {"db": "ok", "llm_config": "..."}
docker compose -f deploy/docker-compose.yml --env-file .env down
```
`--env-file .env` is required on every invocation (`up`, `down`, `logs`, `run`, ...) --
Compose only reads `.env` automatically from the directory the compose file lives in,
not the repo root, and without it `${POSTGRES_PASSWORD}` silently resolves to blank.

**Tests** (stdlib-only `tests/unit/test_matching_*` and `test_fixtures_taxonomy.py`
need nothing installed; `test_config.py` needs the venv above)
```
python3 -m unittest discover -s tests/unit   # or: pytest -q   (inside the venv)
```

**Lint**
```
ruff check app tests
```

**Create a migration / run ingestion / import snapshot / deploy to the VPS**
TODO: T-102 (Alembic baseline), T-210/T-211 (ingestion + snapshot), T-105 (first VPS deploy)
have not landed yet -- these commands don't exist until then.

## Definition of done

Listed AC rows pass; tests added and green; no new warnings in lint; templates have loading, empty, error and success states; the live URL still passes the latest checkpoint.
