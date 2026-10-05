# ARCHITECTURE.md

> How the product is built. Every schema is defined once, in "Schemas"; other sections refer to it by name. Tasks reference **section names**, not numbers. No code in this document; contracts are tables.
> Diagram: `docs/diagrams/architecture.svg`.

## Stack decisions

| Area | Choice | Reason | Rejected |
|---|---|---|---|
| Language/runtime | Python 3.12 | Team skill; LangGraph and Pydantic are Python-first | Node.js |
| Web framework | FastAPI, one process, one worker | Async, typed, simple to host as one container | Django (heavier admin we will not use) |
| Pages | Jinja2 server-rendered pages + HTMX for partial updates and polling | One deployable; no frontend build; no frontend specialist needed | Next.js + separate API |
| Styling | Hand-written CSS with design tokens (primitive → semantic → component); Vazirmatn font self-hosted | No build step; full RTL control | Tailwind via CDN (CDN dependency, not production-grade) |
| Database | PostgreSQL 16 everywhere | One dialect; needed by the checkpointer | SQLite locally |
| ORM / migrations | SQLAlchemy 2 + Alembic | Standard, typed | Raw SQL files |
| Validation | Pydantic v2 for every LLM input/output and form payload | Allowed by C-04; strict schemas | Ad-hoc dicts |
| Agent | LangGraph with the Postgres checkpointer; `interrupt` for user questions | Conditional edges, cycles, persistence and human-in-the-loop out of the box; allowed by C-04 | Hand-rolled state machine (fallback only if G3 shows no one can use LangGraph) |
| LLM client | Official OpenAI Python SDK with `base_url` = `https://openrouter.ai/api/v1` | OpenRouter is OpenAI-compatible; one key, one balance, built-in model fallback | Provider-specific SDKs |
| Scraping | Python batch command (httpx + an HTML parser), run outside user requests | Real data (D-14) with predictable cost and no ban risk during judging | Headless browser; live scraping |
| Password hashing | Argon2 (argon2-cffi) | Current best practice | bcrypt |
| HTML sanitizer | markdown-it-py for Markdown → HTML, then nh3 allowlist sanitizer | Fast, strict | Rendering LLM HTML directly |
| Hosting | Frankfurt VPS, Docker Compose: Caddy (automatic HTTPS) + app + PostgreSQL on an internal network | Team's VPS (D-07); Caddy removes manual certificate work | Managed PaaS; exposing PostgreSQL |

## Topology

| Component | Runs where | Talks to |
|---|---|---|
| Browser | User / judge device (mostly inside Iran) | Caddy over HTTPS only |
| Caddy | VPS, ports 80/443 | App on the internal Docker network |
| App container | VPS | PostgreSQL, OpenRouter |
| PostgreSQL 16 | VPS, internal network only, named volume | App only |
| OpenRouter | External, OpenAI-compatible | Called only by `app/llm/` |
| Ingestion command | VPS (or a machine in Iran if the source blocks Frankfurt, then the snapshot is uploaded) | Source site; OpenRouter (enrichment); PostgreSQL |
| Backup copy | Off the VPS (a team laptop or object storage) | Pulled nightly |
| Uptime monitor | External service | `GET /healthz` every 5 min |

Firewall: only 22 (key-only SSH), 80 and 443 open. All static files (CSS, fonts, HTMX) are served by the app. No CDN.

## Repo layout

| Path | Contents |
|---|---|
| `app/main.py` | App factory, middleware, startup (migrate check, stale-run recovery) |
| `app/config.py` | Typed settings from environment; fails fast on missing values |
| `app/db/` | Engine, session, SQLAlchemy models |
| `alembic/` | Migrations |
| `app/auth/` | Sign-up, login, logout, sessions, rate limit |
| `app/profile/` | Profile forms, evidence items, privacy notice |
| `app/jobs/` | Listing repository, snapshot import |
| `app/ingest/` | `sources/<site>` (list + detail parsing), `clean` (PII strip, normalization), `enrich` (FAST model, batched), `dedupe`, `snapshot` (export/import) |
| `app/matching/` | `normalize`, `filters`, `scoring`, `diff`, `relax` (all deterministic) |
| `app/agent/` | `state` (typed graph states), `graphs/match`, `graphs/feedback`, `graphs/resume`, `graphs/extract`, `tools`, `runner`, `verify` |
| `app/llm/` | Adapter, tier routing, failover, structured output + repair, budget guard, usage log, fault injection |
| `app/prompts/` | One Markdown file per prompt, first line `version: N` |
| `app/web/` | Routes, `templates/`, `static/` (tokens.css, app.css, htmx, fonts) |
| `app/security/` | CSRF, sanitizer, ownership helpers |
| `data/taxonomy/` | `skills.json`: ~300 canonical skills across the six paths with Persian and English aliases; `paths.json` |
| `data/snapshot/` | Frozen enriched snapshot (git-ignored; never in a public repo) |
| `tests/fixtures/` | `jobs_fixtures.json` (J01–J08), personas |
| `deploy/` | `docker-compose.yml`, `Caddyfile`, backup script notes |
| `tests/unit/`, `tests/integration/`, `tests/agent/` | Unit, HTTP-level, and mocked-LLM agent tests; `tests/agent/eval_cases.md` |
| `Dockerfile`, `pyproject.toml`, `.env.example` | Build and configuration |

## Schemas

All IDs are UUIDs except listing IDs (`<source>-<id>`; fixtures `J01`…`J08`). All timestamps are UTC. Money is integer Toman per month.

### users
| Field | Type | Notes |
|---|---|---|
| id | uuid | PK |
| email | text | unique, stored lowercase |
| password_hash | text | Argon2 |
| created_at | timestamp | |

### sessions
| Field | Type | Notes |
|---|---|---|
| id | text | SHA-256 of the random cookie token; PK |
| user_id | uuid | FK users |
| csrf_token | text | random per session |
| expires_at | timestamp | `SESSION_TTL_HOURS` |

### login_attempts
| Field | Type | Notes |
|---|---|---|
| key | text | email (lowercase) |
| window_start | timestamp | 15-minute window |
| count | int | |

### profiles
| Field | Type | Notes |
|---|---|---|
| user_id | uuid | PK, FK users |
| target_path | enum CareerPath | required; exactly one |
| full_name | text | required |
| city | text | required, normalized |
| relocate | bool | default false |
| seniority | enum Seniority | required |
| years_experience | numeric(3,1) | ≥ 0 |
| remote_pref | enum RemotePref | required |
| work_types | set of WorkType | ≥ 1 |
| salary_floor_toman | int | nullable |
| resume_language | enum fa, en | default fa; chosen again per draft |
| military_status | enum MilitaryStatus | default not_applicable (Could) |
| links | list of URL | optional |
| free_text | text | ≤ 1,000 chars |
| privacy_ack_at | timestamp | set when the notice is acknowledged |

### evidence items (four tables, same pattern)
Every item has `id`, `user_id`, `source` (form, extract, agent_answer, feedback), `confirmed` (bool), `created_at`. Only `confirmed = true` items are evidence.

| Table | Extra fields |
|---|---|
| skills | name_canonical (text), display_name |
| projects | title, description (≤ 600), technologies (list of canonical skills), link |
| education | degree, field, institution, year |
| experiences | title, organization, period_text, bullets (list, each ≤ 200) |

Evidence reference format used by the agent: `skill:<id>`, `project:<id>`, `education:<id>`, `experience:<id>`.

### jobs
| Field | Type | Notes |
|---|---|---|
| id | text | `<source>-<source_listing_id>`; fixtures `J01`…`J08` |
| source | text | site key |
| source_url | text | unique; link shown to users |
| fetched_at | timestamp | shown as fetch date |
| title, company | text | from the listing |
| path | enum CareerPath | from enrichment |
| city | text | nullable for remote |
| arrangement | enum Arrangement | |
| work_type | enum WorkType | |
| seniority | enum Seniority | |
| required_skills, preferred_skills | list of canonical skills | either may be empty |
| salary_min_toman, salary_max_toman | int | both null when unknown or «توافقی» |
| excerpt_fa | text | ≤ 600 chars, PII removed |
| enrichment_confidence | map field → 0–1 | fields < 0.6 display «نامشخص» |
| enrichment_version | int | prompt version used |
| is_fixture | bool | true only in the test database |
| active | bool | |

### search_sessions
| Field | Type | Notes |
|---|---|---|
| id | uuid | PK |
| user_id | uuid | |
| context | SearchContext (below) | typed JSON |
| created_at, updated_at | timestamp | |

**SearchContext** (only these fields may be changed by feedback):

| Field | Type | Default |
|---|---|---|
| remote_pref | RemotePref | from profile |
| salary_floor_toman | int or null | from profile |
| work_types | set of WorkType | from profile |
| max_seniority | Seniority or null | null |
| hidden_job_ids | set of text | empty |
| emphasis_skills | set of canonical skills | empty |

### runs
| Field | Type | Notes |
|---|---|---|
| id | uuid | also the LangGraph `thread_id` |
| user_id | uuid | |
| kind | enum extract, match, feedback, resume, revise | |
| search_session_id | uuid | nullable |
| parent_run_id | uuid | previous match run (for diffs) or the draft's run |
| status | enum RunStatus | |
| steps | list of {key, label_fa, state, note_fa} | rendered in the agent pane |
| decisions | list of {type, text_fa} | the agent trace |
| mode | enum normal, simplified | |
| error_code | text | nullable |
| created_at, finished_at | timestamp | |

Constraint: at most one run per user with status `queued` or `running` (partial unique index).

### match_results
| Field | Type | Notes |
|---|---|---|
| id | uuid | |
| run_id | uuid | |
| job_id | text | |
| rank | int | 1-based |
| score | int | 0–100 |
| label | enum strong, possible, weak | |
| matched | list of skills | |
| gaps_required, gaps_preferred | list of skills | |
| considerations | list of text_fa | e.g., «حقوق: نامشخص» |
| explanation_fa | text | ≤ 2 sentences |
| explanation_source | enum llm, template | |
| previous_rank | int or null | from the parent run |

`excluded_results` has the same `run_id`, `job_id`, plus `reason_code` and `reason_fa`.

### feedback and feedback_effects
| feedback field | Type | Notes |
|---|---|---|
| id, user_id, run_id | uuid | |
| job_id | text | nullable; set for per-card quick feedback |
| kind | enum quick, text | |
| quick_reason | enum not_relevant, salary_low, not_remote, too_senior, missing_skills | |
| text | text | ≤ 500 chars |
| status | enum received, needs_clarification, applied, no_change | |

| feedback_effects field | Type | Notes |
|---|---|---|
| feedback_id | uuid | |
| target | enum search, profile | |
| field | enum (SearchContext fields) or `profile.skills` | allowlist only |
| op | enum set, add, remove | |
| old_value, new_value | typed JSON | |

### agent_questions
| Field | Type | Notes |
|---|---|---|
| id, run_id | uuid | |
| kind | enum clarify, evidence, relax | |
| question_fa | text | |
| options_fa | list of text | may be empty |
| about | text | skill or field concerned |
| answer | typed JSON | null until answered |
| status | enum open, answered, skipped | |

### resume_drafts and resume_claims
| resume_drafts field | Type | Notes |
|---|---|---|
| id, user_id, run_id | uuid | |
| job_id | text | |
| version | int | starts at 1; max 3 (1 + 2 revisions) |
| language | enum fa, en | |
| sections | typed JSON | header, summary, skills, projects, experience, education |
| plain_text | text | for copy |
| verification | {checked, removed, rewrite_rounds, notes_fa} | |

| resume_claims field | Type | Notes |
|---|---|---|
| draft_id | uuid | |
| section, text | text | one bullet or sentence |
| evidence_refs | list of refs | ≥ 1 |
| status | enum kept, removed | |
| removal_reason | text | nullable |

### llm_usage
| Field | Type |
|---|---|
| id, user_id, run_id | uuid |
| purpose | text (prompt name) |
| tier | enum fast, smart |
| model_used | text (as reported by OpenRouter, shows fallbacks) |
| model | text |
| input_tokens, output_tokens, latency_ms | int |
| ok | bool |
| error_code | text |
| est_cost_usd | numeric |
| created_at | timestamp |

## Enums and mappings

| Enum | Values (order matters where noted) |
|---|---|
| CareerPath | frontend, backend, fullstack, mobile, devops, data_ai |
| Seniority (ordered) | intern < junior < mid < senior |
| RemotePref | remote_only, remote_or_hybrid, any |
| Arrangement | remote, hybrid, onsite |
| WorkType | full_time, part_time, internship, contract |
| RunStatus | queued, running, awaiting_user, succeeded, failed, cancelled |
| MilitaryStatus | not_applicable, completed, exempt, in_progress, prefer_not_to_say |

Arrangement acceptance (H1):

| RemotePref | remote | hybrid / onsite in user's city | hybrid / onsite elsewhere |
|---|---|---|---|
| remote_only | accept | exclude | exclude |
| remote_or_hybrid | accept | hybrid accept, onsite exclude | accept only if `relocate` |
| any | accept | accept | accept only if `relocate` |

## Normalization

Applied to every user input and to every listing during ingestion.

| Rule | Detail |
|---|---|
| Characters | Arabic «ي»→«ی», «ك»→«ک»; remove kashida; collapse spaces |
| ZWNJ | Kept for display; removed in matching keys |
| Digits | Persian and Arabic digits → ASCII before number parsing |
| Money | «۲۵ میلیون», "25M", "25 تومن" → 25,000,000 Toman; values stated in «ریال» are divided by 10 |
| Skills | Lowercase Latin, strip punctuation, map through `data/taxonomy/skills.json` (e.g., reactjs, ری‌اکت → React; جنگو → Django; k8s → Kubernetes; پایتون → Python). Unknown skills are kept as entered and flagged «ناشناخته»; the enrichment step may map them to a canonical skill |
| City | Canonical list of Iranian province capitals + "other" |

## Ingestion

Batch only (D-14, D-22). Command run by A; never triggered by a user request.

| Step | Type | Does |
|---|---|---|
| I1 discover | tool | Walk the source's category or search pages for the six paths; collect listing URLs; obey robots.txt; ≥ 3 s between requests; stop at `INGEST_MAX_LISTINGS` |
| I2 fetch + parse | tool | Fetch each listing once; parse the site's structured fields (title, company, city, contract type, salary text, seniority text, description) |
| I3 clean | tool | Remove phone numbers, emails and personal names; normalize Persian text; parse salary («توافقی» → unknown); cut the excerpt |
| I4 skills | tool | Map skill mentions through the taxonomy |
| I5 enrich | LLM (FAST), batches of 5 listings | Fill path, arrangement, seniority, required vs preferred skills, missing city; per-field confidence; schema-validated |
| I6 dedupe + store | tool | Upsert by `source_url`; skip unchanged pages by content hash |
| I7 snapshot | tool | Export / import the enriched set; freeze by noon of day 4 |

Cost control: a page already enriched with the current `enrichment_version` is never sent to the LLM again. Expected cost ≤ $0.75 for ~500 listings (D-19).

### Source profile (filled at G4)

| Item | Value |
|---|---|
| Site | TODO(G4) |
| Discovery | TODO(G4): sitemap URL or category URL patterns allowed by robots.txt |
| Detail URL pattern | TODO(G4) |
| Delay between requests | ≥ 5 s |
| Field mapping | TODO(G4): selector or label for title, company, city, contract type, seniority, salary, description |
| Sample pages | `tests/fixtures/html/<site>/` (10 pages) |
| Scraping location | VPS, or a machine in Iran if G4 check 1–3 fails from Frankfurt |

## Matching

Deterministic. No LLM call (SR-10). Input: profile evidence + SearchContext + active listings.

### Hard filters (exclude and record a Persian reason)

| ID | Rule | reason_code |
|---|---|---|
| H0 | Listing path ≠ profile `target_path` (counted, not listed) | path |
| H1 | Arrangement acceptance table above | arrangement |
| H2 | Floor set and listing `salary_max` known and `< floor` | salary |
| H3 | Listing seniority two or more levels above the user's (or above `max_seniority` when set) | seniority |
| H4 | Listing work type not in the context's `work_types` | work_type |
| H5 | Listing in `hidden_job_ids` | hidden |
| H6 | (Could) Listing requires military clearance and status is `in_progress` | military |

### Score (0–100, rounded half-up to an integer)

Let S = user's confirmed skills, R = required, P = preferred, E = emphasis skills.

| Component | Base weight | Value |
|---|---:|---|
| Required skills | 50 | \|S∩R\| / \|R\|; if R is empty, value 1.0 and consideration «نیازمندی‌ها مشخص نشده» |
| Preferred skills | 15 | \|S∩P\| / \|P\|; if P is empty, this weight moves to Required |
| Emphasis | 5 | \|E∩(R∪P)\| / \|E\|; if E is empty, this weight moves to Required |
| Seniority fit | 15 | same level 1.0; listing one below 0.8; one above 0.5; two or more below 0.5 |
| Salary fit | 10 | unknown or no floor 0.5; `salary_min ≥ floor` 1.0; `salary_max ≥ floor > salary_min` 0.6 |
| Arrangement fit | 5 | remote 1.0; accepted hybrid/onsite 0.6 |

Labels: ≥ 75 strong (قوی), 50–74 possible (متوسط), 35–49 weak (ضعیف), < 35 not displayed. Display at most `MAX_RESULTS` (5). Tie-break: score desc, then listing ID asc.

Three tiers per result: matched = S∩(R∪P); gaps_required = R−S; gaps_preferred = P−S; dealbreakers appear only as exclusion reasons.

### Properties (unit-tested)

| Property | Statement |
|---|---|
| Bounds | Every score is in [0, 100] |
| Determinism | Same inputs → same results and order |
| Monotonic filters | Adding a constraint never adds a listing to the result set |
| Idempotent normalization | normalize(normalize(x)) = normalize(x) |
| No division by zero | Empty R, P or E never raises |

### Diff (for "what changed")

Compares a run with its parent: listings that left (with exclusion reason), joined, and moved (old rank → new rank), plus the feedback effects that caused the run.

### Relaxation search (DP-1, deterministic part)

Candidate relaxations: lower the salary floor to the highest value that yields ≥ 3 displayable results; widen RemotePref one step; remove `max_seniority`. Pick the candidate with the largest gain; ties prefer salary, then arrangement. If no candidate yields a gain, no proposal is made.

## Agent design

Four LangGraph graphs, all compiled with the Postgres checkpointer. `thread_id` = `runs.id`. Every node appends to `runs.steps` and, when it decides something, to `runs.decisions`. User questions use `interrupt`; the run status becomes `awaiting_user` and the answer resumes the same thread.

### Match graph (kind = match)

| Node | Type | Does |
|---|---|---|
| M1 load | tool | Load profile evidence, SearchContext, listings |
| M2 normalize | tool | Normalization rules |
| M3 filter | tool | H0–H6, record exclusions (path mismatches only counted) |
| M4 enough? | edge | (Could, DP-1) displayable < 3 and no proposal yet in this run → M4a; else M5. Without DP-1: M5 with empty-state guidance |
| M4a propose_relax | tool + LLM (fast) + interrupt | Relaxation search; LLM writes one Persian sentence; asks accept/keep; accept → update SearchContext → M3 |
| M5 score | tool | Scores, labels, tiers, top `MAX_RESULTS` |
| M6 explain | LLM (smart) | One batched call for all shown results; input is the computed facts only |
| M7 ground_check | tool | Each explanation may name only skills/cities/salaries present in that result's facts; failures → template for that listing |
| M8 diff | tool | Diff against parent run |
| M9 persist | tool | Write results, excluded results, decisions |

### Feedback graph (kind = feedback)

| Node | Type | Does |
|---|---|---|
| F1 map_quick | tool | Quick reasons map without LLM: not_relevant → hide listing; not_remote → `remote_only`; too_senior → `max_seniority` = user's level; missing_skills → hide listing; salary_low → F3 |
| F2 parse | LLM (fast) | Free text → list of intents `{target, field, op, value, confidence}` + `needs_clarification`; numbers go through the money normalizer |
| F2b validate | tool | Drop any intent outside the allowlist; confidence < 0.7 or missing value → F3 |
| F3 clarify | interrupt | One question with options (e.g., floor +5M / +10M / custom); answer → F2; max 2 rounds, then status `no_change` |
| F4 apply | tool | Write effects (search vs profile per D-16) |
| F5 rerun | tool | Start a child match run with `parent_run_id` |

### Resume graph (kind = resume; revise re-enters at R5)

| Node | Type | Does |
|---|---|---|
| R1 load | tool | Profile evidence, listing, match facts |
| R2 gaps | tool | Required then preferred skills without evidence; keep at most 3 |
| R3 ask | LLM (fast) + interrupt | Write the questions; pause for answers (answer or skip each) |
| R4 absorb | LLM (fast) + tool | Turn answers into new confirmed evidence (`source = agent_answer`) or nothing |
| R5 generate | LLM (smart) | Sections as structured output in the chosen language (fa RTL / en LTR); every claim carries `evidence_refs`; Persian evidence is translated, never embellished; revision instruction (if any) applied |
| R6 verify | tool (+ LLM fast, Should) | Rules V1–V4 below; unsupported claims removed |
| R7 again? | edge | Claims removed and rounds < 2 → R5 with the removal list; else R8 |
| R8 finalize | tool | Render, sanitize, store version, verification report |

Verification rules:

| ID | Rule |
|---|---|
| V1 | Every claim has ≥ 1 evidence ref that exists and belongs to the user |
| V2 | Every skill named in the claim is in the referenced items or in confirmed skills |
| V3 | Every number, date, organization and institution in the claim appears in the referenced item's text |
| V4 | (Should) Fast-tier entailment check: "is this claim supported by this evidence text?" — "no" removes the claim |

Fabrication instructions in a revision are detected in R5's structured output (`refused_instruction` with a Persian reason) and also blocked by V1–V3.

### Extract graph (kind = extract)

E1 LLM (fast) turns pasted Persian or English text into draft skills, projects, education and experience (`confirmed = false`); E2 tool normalizes; the user confirms items on the profile page. Preferences are never extracted (D-21).

### Prompt rules

| Rule | Detail |
|---|---|
| Location | `app/prompts/<name>.md`, first line `version: N` |
| Structure | Role, context, task, output schema, constraints; user content wrapped in `<user_data>` tags and declared as data, not instructions |
| Inputs | Only the fields the step needs; never the whole profile when a subset suffices |
| Outputs | JSON matching a Pydantic model; nothing else |
| Language | Persian output unless `resume_language = en` |

## LLM access

| Item | Value |
|---|---|
| Endpoint | OpenRouter, `https://openrouter.ai/api/v1`, OpenAI SDK |
| Adapter | `app/llm/` only; every call has `purpose`, `tier`, `user_id`, `run_id` |
| Tiers | `FAST` (extract, enrich, parse, question wording, entailment); `SMART` (explain, generate) |
| Model choice (G1) | Each tier: one primary + one fallback from a different provider, sent as OpenRouter's ordered `models` list; `require_parameters` on, so JSON-schema requests route only to providers that support them |
| Cost target | One golden flow ≈ 25k input + 7k output tokens; must cost ≤ $0.02 (e.g., ≤ ~$0.30 per million input and ≤ ~$1.20 per million output tokens on average). Measured at G1, not assumed |
| Timeouts | FAST 20 s, SMART 40 s |
| Retries | 1 retry on timeout / 429 / 5xx with jittered backoff (model fallback happens inside OpenRouter), then error |
| Structured output | JSON schema; validate with Pydantic; one repair attempt; then error |
| Budget | OpenRouter key credit limit = $5. In-app guard before each call: per-user daily calls (`LLM_DAILY_CALLS_PER_USER`) and global daily cost (`LLM_DAILY_BUDGET_USD`), computed from the `usage` returned with each response; over a cap → `budget_exceeded` |
| Usage log | One `llm_usage` row per call |
| Concurrency | Semaphore `LLM_MAX_CONCURRENCY` (default 4) |
| Fault injection | `FAULT_INJECTION` = `off`, `timeout` or `error`; refused at startup when `APP_ENV=production` |

## Execution model

| Item | Rule |
|---|---|
| Start | POST creates a `runs` row (`queued`) and schedules an asyncio task in the same process |
| One active run | Partial unique index; a second start returns the existing run |
| Awaiting user | Starting a new run of the same kind cancels an `awaiting_user` one |
| Progress | The run page polls `GET /runs/{id}/status` via HTMX every 1.5 s while `queued`/`running`; polling stops on terminal states and on `awaiting_user` (question form shown) |
| Restart recovery | On startup, runs `queued`/`running` older than `RUN_STALE_AFTER_S` become `failed` with `error_code = interrupted`; retry starts a new run |
| Latency budget | Match: M1–M5 ≤ 1 s, M6 ≤ 25 s, rest ≤ 1 s. Resume: R3 ≤ 10 s, R5 ≤ 35 s, R6 ≤ 10 s per round |

## Routes

All pages server-rendered; partials return HTML fragments for HTMX. Every POST requires CSRF. Every `{id}` is checked for ownership; foreign IDs return 404.

| Method | Path | Purpose |
|---|---|---|
| GET | `/` | Landing |
| GET, POST | `/signup`, `/login` | Auth forms |
| POST | `/logout` | End session |
| GET | `/app` | Dashboard: next action, latest run, drafts |
| GET, POST | `/profile` | Profile and evidence items; privacy notice |
| POST | `/profile/extract` | Start extract run |
| POST | `/profile/items/{id}/confirm` | Confirm a draft item |
| POST | `/search` | Start match run |
| GET | `/runs/{id}` | Run page (results or resume) |
| GET | `/runs/{id}/status` | Partial: steps, decisions, question form, or final content |
| POST | `/runs/{id}/answer` | Answer or skip an open question (resumes the graph) |
| POST | `/runs/{id}/feedback` | Quick (with `job_id`) or text feedback → feedback run |
| GET | `/jobs/{job_id}?run={id}` | Listing detail with that run's explanation |
| POST | `/jobs/{job_id}/resume` | Start resume run (with `language` = fa or en) |
| GET | `/drafts/{id}` | Resume view with versions and verification report |
| POST | `/drafts/{id}/revise` | Start revise run (max 2 per draft) |
| GET | `/drafts/{id}/print` | A4 print view |
| GET | `/healthz` | `{db: ok, llm_config: ok}`; no secrets; no LLM call |

## UI system

| Item | Rule |
|---|---|
| Layout | Split workspace: main pane (results / resume) and agent pane (steps, decisions, questions). Desktop: two columns; ≤ 768 px: agent pane stacks below |
| Direction | `<html lang="fa" dir="rtl">`; English tokens wrapped for LTR isolation |
| Tokens | Primitive (colors, sizes) → semantic (`--color-success`, `--color-warning`, `--color-danger`, `--space-*`) → component; no raw hex in component CSS |
| Tiers | Matched = success + check icon; gaps = warning + clock icon; excluded = danger + x icon; always with text |
| States | Each partial has loading, empty, error and success variants |
| Copy | All Persian strings live in templates; tone: short, respectful, no hype |
| Assets | `htmx.min.js` and Vazirmatn `woff2` vendored under `static/` |

## Security

| Threat | Control |
|---|---|
| Credential theft | Argon2; session cookie `HttpOnly`, `Secure`, `SameSite=Lax`; 32-byte random tokens, only their hash stored |
| CSRF | Per-session token in forms and in the `HX-` request header |
| Brute force | `login_attempts` window (AC-AUTH-008) |
| IDOR | Every query filters by `user_id` from the session; IDs from LLM output are never trusted |
| XSS | Jinja autoescape; LLM and user Markdown → HTML → nh3 allowlist (no scripts, no `javascript:` URLs, no inline styles) |
| Prompt injection | Untrusted text delimited as data; outputs only through schemas; effects only through the allowlist; tools receive `user_id` from the session, never from the model |
| Secret leakage | Keys only in environment; logs carry IDs, purposes, timings, error codes — never prompt bodies, profile text or keys |
| Cost abuse | Budget guard in "LLM access" |

## Fallback mode

| Situation | Behavior |
|---|---|
| M6 explain fails after retries/fallback | Template explanations from facts; `runs.mode = simplified`; badge «حالت ساده» |
| F2 parse fails | Quick reasons still work (F1); text feedback shows a Persian error with retry |
| Resume generation fails | Persian error + retry; no partial draft marked final |
| Budget exceeded | LLM features show the limit message; deterministic features continue |

## Observability

Structured JSON logs (request id, user id, run id, event, duration, error code). Events: `signup`, `login_failed`, `run_started`, `step_done`, `run_failed`, `interrupt_opened`, `interrupt_answered`, `feedback_applied`, `claim_removed`, `budget_exceeded`. Daily cost = sum of `llm_usage.est_cost_usd`.

## Deployment

| Item | Rule |
|---|---|
| Compose services | `caddy` (80/443, automatic certificates), `app` (non-root, one uvicorn worker), `db` (PostgreSQL 16, named volume, no published port) |
| Host name | Cheap domain or a wildcard-DNS name for the VPS IP, required for the certificate |
| Start sequence | Alembic upgrade → checkpointer setup → snapshot import if the jobs table is empty → serve |
| Configuration | `.env` on the VPS (mode 600), never in git; production refuses to start with fault injection on or missing secrets |
| Server hardening | Key-only SSH, firewall 22/80/443, automatic security updates, Docker restart policy `unless-stopped` |
| Backups | Nightly `pg_dump` copied **off the VPS**; one restore rehearsal (AC-DEPLOY-004) |
| Monitoring | External uptime check on `/healthz` every 5 min with alert; daily look at `llm_usage` cost |
| Reachability | Test from two Iranian networks on day 1 and before submission (AC-DEPLOY-007) |
| Release | Code freeze on the last day at 12:00; after that only fixes for Blocker criteria |

## Failure modes

| Failure | Detection | Response |
|---|---|---|
| Model or provider down | Timeouts / 5xx | OpenRouter `models` fallback → one retry → simplified mode or error |
| Gateway returns invalid JSON | Pydantic error | One repair → error |
| Server restart mid-run | Startup scan | Run marked failed; retry button |
| Duplicate submit | Unique index | Return existing run |
| DB unreachable | `/healthz` fails | Monitor alert; container restart policy; restore from off-VPS backup |
| Budget exhausted | Budget guard | Limit message; alert in logs |
| Credit runs out during judging | Usage log + daily check + OpenRouter key limit | «حالت ساده» for search; resume shows "try tomorrow"; owner decides on a top-up |
| Source site blocks the scraper | HTTP 403/429 or empty pages | Stop; continue from a machine in Iran; or ship with the listings already collected |

## Cut list

Cut from the top when an evening checkpoint is missed. Never cut: auth, profile with extraction, ingestion of at least 300 listings, matching, M6–M7, feedback graph, DP-2, resume graph, DP-3, DP-4, fa/en resume, deploy, golden E2E.

| Order | Cut | Effect |
|---|---|---|
| 1 | Could items (DP-1, H6 military, embeddings, delete-my-data) | None on Must criteria |
| 2 | Mobile layout polish | AC-UX-004 dropped |
| 3 | V4 entailment check | V1–V3 still enforce honesty |
| 4 | Revisions reduced from 2 to 1 | AC-APP-006 adjusted |
| 5 | Paths reduced from 6 to 3 (frontend, backend, data & AI) | AC-DATA-001 adjusted; record in DECISIONS |
| 6 | Live evaluation run reduced to 5 cases | Evaluation set adjusted |

## AC map

| Area | Components |
|---|---|
| AC-AUTH | `app/auth`, sessions, login_attempts |
| AC-PROF | `app/profile`, evidence tables, Normalization |
| AC-DATA | Ingestion, `app/ingest/`, snapshot import |
| AC-MATCH | `app/matching`, Match graph M3–M7 |
| AC-AGENT | runner, Match graph M4/M4a, Fallback mode, agent pane |
| AC-FBK | Feedback graph, Diff |
| AC-APP | Resume graph, Verification rules, print view |
| AC-UX | UI system |
| AC-SEC | Security |
| AC-REL | Execution model, LLM access, Fallback mode |
| AC-DEPLOY | Deployment, Topology |

## Open decisions

| ID | Decision | Resolved at |
|---|---|---|
| O-01 | OpenRouter model IDs for FAST/SMART (primary + fallback) | G1 |
| O-02 | Host name, HTTPS, reachability from Iran | G2 |
| O-07 | Source site and scraping location | G4 |
